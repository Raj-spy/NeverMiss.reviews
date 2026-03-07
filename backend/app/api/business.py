# backend/app/api/business.py
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from supabase import Client
from typing import List
from collections import defaultdict
import uuid

from ..models.schemas import BusinessCreate, BusinessResponse, MessageResponse
from ..core.database import get_supabase_client
from ..core.deps import get_current_user
from ..services.apify_service import scrape_reviews_for_business
from ..services.ai_service import generate_replies_for_business

router = APIRouter(prefix="/business", tags=["Business"])

# ─── URL Validation ───────────────────────────────────────────────────────────

VALID_MAPS_PATTERNS = [
    "google.com/maps",
    "goo.gl/maps",
    "maps.google.com",
]

INVALID_MAPS_PATTERNS = [
    "share.google",
]

def _validate_maps_url(url: str) -> bool:
    url_lower = url.lower()
    if any(p in url_lower for p in INVALID_MAPS_PATTERNS):
        return False
    return any(p in url_lower for p in VALID_MAPS_PATTERNS)


# ─── Background Task ─────────────────────────────────────────────────────────

async def scrape_and_generate_replies(
    business_id: str,
    google_maps_url: str,
    db: Client,
    is_initial: bool = False,
):
    """
    Orchestrates: scrape → store new reviews → generate AI replies.
    is_initial=True  → 500 reviews (first time business added)
    is_initial=False → 20 reviews (scheduled / manual refresh)
    """
    try:
        new_review_ids = await scrape_reviews_for_business(
            business_id, google_maps_url, db, is_initial=is_initial
        )
        if new_review_ids:
            await generate_replies_for_business(new_review_ids, db)
    except Exception as e:
        print(f"[ERROR] scrape_and_generate_replies failed for {business_id}: {e}")


# ─── Routes ──────────────────────────────────────────────────────────────────

@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreate,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Add a new business. Validates Google Maps URL.
    Triggers full historical scrape (500 reviews) in background.
    """
    if not _validate_maps_url(payload.google_maps_url):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid Google Maps URL. Please copy the URL directly from your "
                "browser address bar (e.g. https://www.google.com/maps/place/...). "
                "Share links are not supported."
            ),
        )

    business_id = str(uuid.uuid4())
    record = {
        "id": business_id,
        "user_id": current_user["id"],
        "business_name": payload.business_name,
        "google_maps_url": payload.google_maps_url,
        "description": payload.description or "",
    }

    result = db.table("businesses").insert(record).execute()
    business = result.data[0]

    # is_initial=True — full 500 review historical scrape
    background_tasks.add_task(
        scrape_and_generate_replies,
        business_id,
        payload.google_maps_url,
        db,
        is_initial=True,
    )

    return BusinessResponse(**business, review_count=0)


@router.get("", response_model=List[BusinessResponse])
def list_businesses(
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    List all businesses for current user.
    Fetches review stats in one bulk query.
    """
    businesses = (
        db.table("businesses")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if not businesses:
        return []

    biz_ids = [b["id"] for b in businesses]

    all_reviews = (
        db.table("reviews")
        .select("business_id, rating")
        .in_("business_id", biz_ids)
        .execute()
        .data
    )

    reviews_by_biz: dict = defaultdict(list)
    for r in all_reviews:
        reviews_by_biz[r["business_id"]].append(r["rating"])

    result = []
    for biz in businesses:
        ratings = reviews_by_biz.get(biz["id"], [])
        avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None
        result.append(
            BusinessResponse(**biz, review_count=len(ratings), avg_rating=avg_rating)
        )

    return result


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: str,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Get a single business by ID."""
    result = (
        db.table("businesses")
        .select("*")
        .eq("id", business_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Business not found")
    return BusinessResponse(**result.data)


@router.delete("/{business_id}", response_model=MessageResponse)
def delete_business(
    business_id: str,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Delete a business and all associated data."""
    existing = (
        db.table("businesses")
        .select("id")
        .eq("id", business_id)
        .eq("user_id", current_user["id"])
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Business not found")

    db.table("businesses").delete().eq("id", business_id).execute()
    return MessageResponse(message="Business deleted successfully")


@router.post("/{business_id}/refresh", response_model=MessageResponse)
def refresh_reviews(
    business_id: str,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Manually trigger incremental review scrape (latest 20 reviews).
    Use this to check for new reviews since last scrape.
    """
    result = (
        db.table("businesses")
        .select("*")
        .eq("id", business_id)
        .eq("user_id", current_user["id"])
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Business not found")

    if not _validate_maps_url(result.data["google_maps_url"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Saved Google Maps URL is invalid. Please delete and re-add "
                "this business with a valid URL from your browser address bar."
            ),
        )

    # is_initial=False — incremental 20 review scrape
    background_tasks.add_task(
        scrape_and_generate_replies,
        business_id,
        result.data["google_maps_url"],
        db,
        is_initial=False,
    )

    return MessageResponse(message="Review refresh started — checking latest 20 reviews")