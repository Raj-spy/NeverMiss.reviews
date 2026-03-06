# backend/app/services/ai_service.py
# Uses Groq API (Llama models) to generate professional reply suggestions for reviews

import uuid
from typing import List, Optional
from groq import Groq
from supabase import Client

from ..core.config import get_settings

settings = get_settings()


def _get_groq_client() -> Groq:
    return Groq(api_key=settings.groq_api_key)


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
- Return ONLY the reply text

Reply:
"""


async def generate_reply_for_review(review_id: str, db: Client) -> Optional[dict]:

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

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # ✅ Updated Groq supported model
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=200
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


async def generate_replies_for_business(review_ids: List[str], db: Client):

    print(f"[AI] Generating replies for {len(review_ids)} reviews")

    for review_id in review_ids:
        try:
            await generate_reply_for_review(review_id, db)
        except Exception as e:
            print(f"[AI] Failed to generate reply for review {review_id}: {e}")

    print("[AI] Done generating replies")