# backend/app/api/business.py
# Business profile CRUD routes (multi-tenant: each user manages their own businesses)

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from supabase import Client
from typing import List
import uuid

from ..models.schemas import BusinessCreate, BusinessResponse, MessageResponse
from ..core.database import get_supabase_client
from ..core.deps import get_current_user
from ..services.apify_service import scrape_reviews_for_business
from ..services.ai_service import generate_replies_for_business

router = APIRouter(prefix="/business", tags=["Business"])


@router.post("", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
def create_business(
    payload: BusinessCreate,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Add a new business for the authenticated user.
    Triggers an initial review scrape in the background.
    """
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

    # Kick off initial scrape asynchronously
    background_tasks.add_task(
        scrape_and_generate_replies, business_id, payload.google_maps_url, db
    )

    return BusinessResponse(**business, review_count=0)


@router.get("", response_model=List[BusinessResponse])
def list_businesses(
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    List all businesses belonging to the current user.
    Includes review count and average rating per business.
    """
    businesses = (
        db.table("businesses")
        .select("*")
        .eq("user_id", current_user["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )

    result = []
    for biz in businesses:
        # Get review stats for each business
        reviews = (
            db.table("reviews")
            .select("rating")
            .eq("business_id", biz["id"])
            .execute()
            .data
        )
        avg_rating = (
            round(sum(r["rating"] for r in reviews) / len(reviews), 1)
            if reviews
            else None
        )
        result.append(
            BusinessResponse(**biz, review_count=len(reviews), avg_rating=avg_rating)
        )

    return result


@router.get("/{business_id}", response_model=BusinessResponse)
def get_business(
    business_id: str,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Get a single business by ID (must belong to current user)."""
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
    """Delete a business and all associated reviews/replies."""
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
    """Manually trigger a review scrape for a business."""
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

    background_tasks.add_task(
        scrape_and_generate_replies, business_id, result.data["google_maps_url"], db
    )

    return MessageResponse(message="Review refresh started in background")


# ─── Helper ──────────────────────────────────────────────────────────────────

async def scrape_and_generate_replies(business_id: str, google_maps_url: str, db: Client):
    """
    Orchestrates: scrape → store new reviews → generate AI replies.
    Called in background tasks to avoid blocking the API response.
    """
    try:
        new_review_ids = await scrape_reviews_for_business(business_id, google_maps_url, db)
        if new_review_ids:
            await generate_replies_for_business(new_review_ids, db)
    except Exception as e:
        print(f"[ERROR] scrape_and_generate_replies failed for {business_id}: {e}")
