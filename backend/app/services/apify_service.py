# backend/app/services/apify_service.py
# Uses Apify Google Maps Reviews Scraper to fetch reviews

import uuid
from typing import List
from apify_client import ApifyClient
from supabase import Client

from ..core.config import get_settings

settings = get_settings()


def _get_apify_client() -> ApifyClient:
    return ApifyClient(settings.apify_api_token)


async def scrape_reviews_for_business(
    business_id: str,
    google_maps_url: str,
    db: Client,
) -> List[str]:

    print(f"[Apify] Starting scrape for business {business_id}")

    client = _get_apify_client()

    run_input = {
        "startUrls": [{"url": google_maps_url}],
        "maxReviews": 100,
        "reviewsSort": "newest",
        "language": "en"
    }

    try:
        run = client.actor("compass/Google-Maps-Reviews-Scraper").call(
            run_input=run_input
        )
    except Exception as e:
        print(f"[Apify] Actor call failed: {e}")
        return []

    dataset_id = run["defaultDatasetId"]

    reviews_raw = []

    for item in client.dataset(dataset_id).iterate_items():
        if isinstance(item, dict):
            reviews_raw.append(item)

    print(f"[Apify] Fetched {len(reviews_raw)} raw reviews")

    existing = (
        db.table("reviews")
        .select("review_text, rating")
        .eq("business_id", business_id)
        .execute()
        .data
    )

    existing_set = {(r["review_text"], r["rating"]) for r in existing}

    new_review_ids = []

    for raw in reviews_raw:

        review_text = (
            raw.get("text")
            or raw.get("reviewText")
            or raw.get("review")
            or ""
        ).strip()

        rating = int(raw.get("stars") or raw.get("rating") or 0)

        reviewer_name = (
            raw.get("name")
            or raw.get("reviewerName")
            or "Anonymous"
        )

        review_date = (
            raw.get("publishedAtDate")
            or raw.get("publishAt")
            or raw.get("date")
        )

        if not review_text or not rating:
            continue

        if (review_text, rating) in existing_set:
            continue

        review_id = str(uuid.uuid4())

        db.table("reviews").insert({
            "id": review_id,
            "business_id": business_id,
            "reviewer_name": reviewer_name,
            "review_text": review_text,
            "rating": rating,
            "review_date": str(review_date) if review_date else None,
            "processed": False,
        }).execute()

        new_review_ids.append(review_id)
        existing_set.add((review_text, rating))

    print(f"[Apify] Stored {len(new_review_ids)} new reviews for business {business_id}")

    return new_review_ids