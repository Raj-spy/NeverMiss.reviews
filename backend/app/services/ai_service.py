# backend/app/services/ai_service.py
# Uses Groq API (Llama 3.3 70B) to generate professional reply suggestions for reviews

import uuid
import asyncio
from typing import List, Optional
from groq import AsyncGroq
from supabase import Client

from ..core.config import get_settings

settings = get_settings()

_groq_client: Optional[AsyncGroq] = None

def _get_groq_client() -> AsyncGroq:
    global _groq_client
    if _groq_client is None:
        _groq_client = AsyncGroq(api_key=settings.groq_api_key)
    return _groq_client


def _build_reply_prompt(
    review_text: str,
    rating: int,
    business_name: str,
    reviewer_name: str = "Customer",
) -> str:

    tone_guide = {
        1: "very apologetic, empathetic and resolution-focused",
        2: "apologetic and improvement-focused",
        3: "appreciative and constructive",
        4: "warm, thankful and encouraging",
        5: "enthusiastic, warm and celebratory",
    }.get(rating, "professional and helpful")

    return f"""You are a professional customer relations manager for "{business_name}".

A customer named "{reviewer_name}" left the following {rating}-star Google review:

---
{review_text}
---

Write a professional, personalized reply to this review. The tone should be {tone_guide}.

Guidelines:
- Address the reviewer by name if possible
- Keep the reply between 60-120 words
- Acknowledge specific points mentioned in the review
- For negative reviews (1-2 stars): apologize sincerely and offer resolution
- For positive reviews (4-5 stars): express gratitude and invite them again
- End warmly mentioning {business_name}
- Return ONLY the reply text, no extra commentary

Reply:
"""


async def generate_reply_for_review(review_id: str, db: Client) -> Optional[dict]:
    """Generate a single AI reply for one review."""

    review = (
        db.table("reviews")
        .select("*, businesses(business_name)")
        .eq("id", review_id)
        .single()
        .execute()
        .data
    )

    if not review:
        print(f"[AI] Review {review_id} not found")
        return None

    business_name = review["businesses"]["business_name"]
    reviewer_name = review.get("reviewer_name", "Customer")

    prompt = _build_reply_prompt(
        review_text=review["review_text"],
        rating=review["rating"],
        business_name=business_name,
        reviewer_name=reviewer_name,
    )

    try:
        client = _get_groq_client()
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",   # ✅ 70B model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=250,
        )
        reply_text = response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[AI] Groq API error for review {review_id}: {e}")
        return None

    reply_id = str(uuid.uuid4())
    result = db.table("ai_replies").insert({
        "id": reply_id,
        "review_id": review_id,
        "reply_text": reply_text,
        "status": "pending",
    }).execute()

    print(f"[AI] Generated reply for review {review_id}")
    return result.data[0] if result.data else None


async def _generate_single(review_id: str, db: Client, semaphore: asyncio.Semaphore):
    """Semaphore se control karo — rate limit safe."""
    async with semaphore:
        try:
            return await generate_reply_for_review(review_id, db)
        except Exception as e:
            print(f"[AI] Failed for review {review_id}: {e}")
            return None


async def generate_replies_for_business(review_ids: List[str], db: Client):
    """
    Parallel mein replies generate karo with priority ordering.
    
    Priority:
    1. 1-2 star (negative) — sabse pehle
    2. 3 star (neutral)
    3. 4-5 star (positive)
    
    Semaphore=5 — 30 RPM limit ke andar rehta hai.
    """
    print(f"[AI] Generating replies for {len(review_ids)} reviews")

    # Fetch ratings for priority sorting
    reviews = (
        db.table("reviews")
        .select("id, rating")
        .in_("id", review_ids)
        .execute()
        .data
    )

    # Negative reviews pehle — priority
    reviews.sort(key=lambda r: r["rating"])
    sorted_ids = [r["id"] for r in reviews]

    # 5 concurrent — safe for 30 RPM with 70B model
    semaphore = asyncio.Semaphore(5)

    tasks = [
        _generate_single(review_id, db, semaphore)
        for review_id in sorted_ids
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    successful = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    failed = len(results) - successful

    print(f"[AI] Done — {successful} replies generated, {failed} failed")