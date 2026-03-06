# backend/app/api/reviews.py
# Routes for fetching reviews with their AI reply suggestions

from fastapi import APIRouter, HTTPException, Depends, Query
from supabase import Client
from typing import List, Optional

from ..models.schemas import ReviewWithReply, AIReplyResponse, AnalyticsSummary
from ..core.database import get_supabase_client
from ..core.deps import get_current_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.get("", response_model=List[ReviewWithReply])
def get_reviews(
    business_id: Optional[str] = Query(None),
    rating: Optional[int] = Query(None, ge=1, le=5),
    processed: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Fetch reviews for the current user's businesses.
    Supports filtering by business, rating, and processed status.
    """
    # Get all business IDs belonging to this user
    user_businesses = (
        db.table("businesses")
        .select("id, business_name")
        .eq("user_id", current_user["id"])
        .execute()
        .data
    )

    if not user_businesses:
        return []

    biz_map = {b["id"]: b["business_name"] for b in user_businesses}
    biz_ids = list(biz_map.keys())

    # Filter to specific business if requested
    if business_id:
        if business_id not in biz_ids:
            raise HTTPException(status_code=403, detail="Access denied to this business")
        biz_ids = [business_id]

    # Build reviews query
    query = (
        db.table("reviews")
        .select("*")
        .in_("business_id", biz_ids)
        .order("created_at", desc=True)
        .limit(limit)
        .offset(offset)
    )

    if rating is not None:
        query = query.eq("rating", rating)
    if processed is not None:
        query = query.eq("processed", processed)

    reviews = query.execute().data

    # Attach AI replies and business names
    result = []
    for review in reviews:
        reply_data = (
            db.table("ai_replies")
            .select("*")
            .eq("review_id", review["id"])
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )

        reply = AIReplyResponse(**reply_data[0]) if reply_data else None
        result.append(
            ReviewWithReply(
                **review,
                business_name=biz_map.get(review["business_id"]),
                reply=reply,
            )
        )

    return result


@router.get("/analytics", response_model=AnalyticsSummary)
def get_analytics(
    business_id: Optional[str] = Query(None),
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Aggregate stats: total reviews, avg rating, reply statuses, weekly trend.
    """
    user_businesses = (
        db.table("businesses")
        .select("id")
        .eq("user_id", current_user["id"])
        .execute()
        .data
    )

    biz_ids = [b["id"] for b in user_businesses]
    if business_id and business_id in biz_ids:
        biz_ids = [business_id]

    if not biz_ids:
        return AnalyticsSummary(
            total_reviews=0, avg_rating=0.0, pending_replies=0,
            approved_replies=0, reviews_this_week=0, rating_distribution={}
        )

    reviews = (
        db.table("reviews").select("*").in_("business_id", biz_ids).execute().data
    )

    total = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / total, 2) if total else 0.0

    # Rating distribution
    dist = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in reviews:
        dist[r["rating"]] = dist.get(r["rating"], 0) + 1

    # Reviews this week (approximate using last 7 days)
    from datetime import datetime, timedelta
    week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
    reviews_this_week = sum(1 for r in reviews if r["created_at"] >= week_ago)

    # Reply stats
    review_ids = [r["id"] for r in reviews]
    if review_ids:
        all_replies = (
            db.table("ai_replies").select("status").in_("review_id", review_ids).execute().data
        )
        pending = sum(1 for r in all_replies if r["status"] == "pending")
        approved = sum(1 for r in all_replies if r["status"] == "approved")
    else:
        pending = approved = 0

    return AnalyticsSummary(
        total_reviews=total,
        avg_rating=avg_rating,
        pending_replies=pending,
        approved_replies=approved,
        reviews_this_week=reviews_this_week,
        rating_distribution={str(k): v for k, v in dist.items()},
    )
