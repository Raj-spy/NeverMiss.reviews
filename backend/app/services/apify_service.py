 # backend/app/services/apify_service.py
# Uses Apify Google Maps Reviews Scraper to fetch and store reviews

import uuid
import hashlib
from typing import List
from datetime import datetime
from apify_client import ApifyClient
from supabase import Client

from ..core.config import get_settings

settings = get_settings()


def _get_apify_client() -> ApifyClient:
    return ApifyClient(settings.apify_api_token)


def _normalize_url(url: str) -> str:
    """Ensures URL has https:// protocol prefix."""
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url


def _make_review_hash(business_id: str, reviewer_name: str, review_text: str, rating: int) -> str:
    """
    Creates a stable unique fingerprint for a review.
    Used for deduplication instead of fragile (text, rating) tuple matching.
    """
    raw = f"{business_id}|{reviewer_name.lower().strip()}|{review_text.lower().strip()}|{rating}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _parse_review(raw: dict) -> dict | None:
    """
    Normalizes a raw Apify review item into a clean dict.
    Returns None if the review is unusable (missing text or rating).
    """
    review_text = (
        raw.get("text")
        or raw.get("reviewText")
        or raw.get("review")
        or raw.get("snippet")
        or raw.get("body")
        or ""
    ).strip()

    try:
        rating = int(
            raw.get("stars")
            or raw.get("rating")
            or raw.get("reviewRating")
            or raw.get("score")
            or 0
        )
    except (ValueError, TypeError):
        rating = 0

    if not review_text or not (1 <= rating <= 5):
        return None

    reviewer_name = (
        raw.get("name")
        or raw.get("reviewerName")
        or raw.get("author")
        or raw.get("authorName")
        or "Anonymous"
    ).strip()

    review_date = (
        raw.get("publishedAtDate")
        or raw.get("publishAt")
        or raw.get("date")
        or raw.get("reviewDate")
        or raw.get("time")
    )

    return {
        "review_text": review_text,
        "rating": rating,
        "reviewer_name": reviewer_name,
        "review_date": str(review_date) if review_date else None,
    }


async def scrape_reviews_for_business(
    business_id: str,
    google_maps_url: str,
    db: Client,
    is_initial: bool = False,
) -> List[str]:
    """
    Scrapes Google Maps reviews via Apify, deduplicates against DB,
    and bulk-inserts new reviews. Returns list of new review IDs.

    is_initial=True  → Full historical scrape (500 reviews) — runs once when business is added
    is_initial=False → Incremental scrape (20 reviews) — runs on schedule/manual refresh
    """

    # ── Step 1: Normalize URL ─────────────────────────────────────────────────
    google_maps_url = _normalize_url(google_maps_url)

    # ── Step 2: Decide how many reviews to fetch ──────────────────────────────
    if is_initial:
        max_reviews = 500
        scrape_type = "INITIAL (full historical)"
    else:
        max_reviews = 20
        scrape_type = "INCREMENTAL (latest only)"

    print(f"[Apify] Starting {scrape_type} scrape for business {business_id}")
    print(f"[Apify] Fetching up to {max_reviews} reviews")

    # ── Step 3: Run Apify actor ───────────────────────────────────────────────
    client = _get_apify_client()

    run_input = {
        "startUrls": [{"url": google_maps_url}],
        "maxReviews": max_reviews,
        "reviewsSort": "newest",
        "language": "en",
    }

    try:
        run = client.actor("compass/Google-Maps-Reviews-Scraper").call(
            run_input=run_input
        )
    except Exception as e:
        print(f"[Apify] Actor call failed: {e}")
        return []

    # ── Step 4: Collect and parse raw items ───────────────────────────────────
    parsed_reviews = []
    skipped = 0

    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        if not isinstance(item, dict):
            continue

        if "error" in item and len(item) == 1:
            print(f"[Apify] Skipping error item: {item['error'][:120]}")
            continue

        parsed = _parse_review(item)
        if parsed:
            parsed_reviews.append(parsed)
        else:
            skipped += 1

    print(f"[Apify] Parsed {len(parsed_reviews)} valid reviews ({skipped} skipped)")

    if not parsed_reviews:
        _update_scrape_metadata(business_id, 0, db)
        return []

    # ── Step 5: Compute hashes ────────────────────────────────────────────────
    for review in parsed_reviews:
        review["hash"] = _make_review_hash(
            business_id,
            review["reviewer_name"],
            review["review_text"],
            review["rating"],
        )

    incoming_hashes = [r["hash"] for r in parsed_reviews]

    # ── Step 6: Check existing hashes in DB ───────────────────────────────────
    try:
        existing_rows = (
            db.table("reviews")
            .select("review_hash")
            .eq("business_id", business_id)
            .in_("review_hash", incoming_hashes)
            .execute()
            .data
        )
        existing_hashes = {r["review_hash"] for r in existing_rows}
        new_reviews = [r for r in parsed_reviews if r["hash"] not in existing_hashes]
    except Exception:
        # Fallback if review_hash column doesn't exist
        existing_rows = (
            db.table("reviews")
            .select("review_text, rating")
            .eq("business_id", business_id)
            .execute()
            .data
        )
        existing_set = {(r["review_text"], r["rating"]) for r in existing_rows}
        new_reviews = [
            r for r in parsed_reviews
            if (r["review_text"], r["rating"]) not in existing_set
        ]

    # ── Step 7: Filter to only new reviews ────────────────────────────────────
    if not new_reviews:
        print(f"[Apify] No new reviews found for business {business_id}")
        _update_scrape_metadata(business_id, 0, db)
        return []

    print(f"[Apify] {len(new_reviews)} new reviews to store")

    # ── Step 8: Bulk insert ───────────────────────────────────────────────────
    records = []
    for r in new_reviews:
        record = {
            "id": str(uuid.uuid4()),
            "business_id": business_id,
            "reviewer_name": r["reviewer_name"],
            "review_text": r["review_text"],
            "rating": r["rating"],
            "review_date": r["review_date"],
            "review_hash": r["hash"],
            "processed": False,
        }
        records.append(record)

    try:
        db.table("reviews").insert(records).execute()
        new_ids = [r["id"] for r in records]
    except Exception as e:
        print(f"[Apify] Bulk insert failed: {e}")
        new_ids = []
        for record in records:
            try:
                db.table("reviews").insert(record).execute()
                new_ids.append(record["id"])
            except Exception:
                pass
        print(f"[Apify] Fallback inserted {len(new_ids)} reviews")

    print(f"[Apify] Stored {len(new_ids)} new reviews for business {business_id}")

    # ── Step 9: Update scrape metadata ───────────────────────────────────────
    _update_scrape_metadata(business_id, len(new_ids), db)

    return new_ids


def _update_scrape_metadata(business_id: str, new_count: int, db: Client):
    """Updates last_scraped_at and total_reviews_scraped on the business record."""
    try:
        # Get current total
        biz = (
            db.table("businesses")
            .select("total_reviews_scraped")
            .eq("id", business_id)
            .single()
            .execute()
            .data
        )
        current_total = biz.get("total_reviews_scraped", 0) or 0

        db.table("businesses").update({
            "last_scraped_at": datetime.utcnow().isoformat(),
            "total_reviews_scraped": current_total + new_count,
        }).eq("id", business_id).execute()

        print(f"[Apify] Metadata updated — total scraped: {current_total + new_count}")
    except Exception as e:
        print(f"[Apify] Metadata update failed: {e}")