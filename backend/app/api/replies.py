# backend/app/api/replies.py
# Routes for approving, editing, and rejecting AI-generated reply suggestions

from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from datetime import datetime

from ..models.schemas import (
    ApproveReplyRequest, RejectReplyRequest, AIReplyResponse, MessageResponse
)
from ..core.database import get_supabase_client
from ..core.deps import get_current_user

router = APIRouter(prefix="/reply", tags=["Replies"])


def _verify_reply_ownership(reply_id: str, current_user: dict, db: Client) -> dict:
    """
    Confirms the reply belongs to a review owned by the current user.
    Returns the reply record if valid.
    """
    reply = (
        db.table("ai_replies").select("*, reviews(business_id)")
        .eq("id", reply_id).single().execute().data
    )

    if not reply:
        raise HTTPException(status_code=404, detail="Reply not found")

    business_id = reply["reviews"]["business_id"]
    business = (
        db.table("businesses").select("id")
        .eq("id", business_id).eq("user_id", current_user["id"])
        .execute().data
    )

    if not business:
        raise HTTPException(status_code=403, detail="Access denied")

    return reply


@router.post("/approve", response_model=AIReplyResponse)
def approve_reply(
    payload: ApproveReplyRequest,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """
    Approve a reply suggestion, optionally with edited text.
    Updates status to 'approved' and marks the review as processed.
    """
    reply = _verify_reply_ownership(payload.reply_id, current_user, db)

    update_data = {
        "status": "approved",
        "updated_at": datetime.utcnow().isoformat(),
    }

    if payload.edited_text:
        update_data["reply_text"] = payload.edited_text

    updated = (
        db.table("ai_replies")
        .update(update_data)
        .eq("id", payload.reply_id)
        .execute()
        .data[0]
    )

    # Mark the review as processed
    db.table("reviews").update({"processed": True}).eq("id", reply["review_id"]).execute()

    return AIReplyResponse(**updated)


@router.post("/reject", response_model=MessageResponse)
def reject_reply(
    payload: RejectReplyRequest,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Reject a reply suggestion (marks as 'rejected')."""
    _verify_reply_ownership(payload.reply_id, current_user, db)

    db.table("ai_replies").update({
        "status": "rejected",
        "updated_at": datetime.utcnow().isoformat(),
    }).eq("id", payload.reply_id).execute()

    return MessageResponse(message="Reply rejected")


@router.get("/{review_id}", response_model=list[AIReplyResponse])
def get_replies_for_review(
    review_id: str,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Get all AI reply versions generated for a review."""
    # Verify ownership via the review's business
    review = db.table("reviews").select("*, businesses(user_id)").eq("id", review_id).single().execute().data

    if not review or review["businesses"]["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    replies = (
        db.table("ai_replies")
        .select("*")
        .eq("review_id", review_id)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    return [AIReplyResponse(**r) for r in replies]


@router.post("/{review_id}/regenerate", response_model=AIReplyResponse)
async def regenerate_reply(
    review_id: str,
    db: Client = Depends(get_supabase_client),
    current_user: dict = Depends(get_current_user),
):
    """Request a new AI-generated reply for an existing review."""
    review = db.table("reviews").select("*, businesses(user_id, business_name)").eq("id", review_id).single().execute().data

    if not review or review["businesses"]["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Access denied")

    from ..services.ai_service import generate_reply_for_review
    new_reply = await generate_reply_for_review(review_id, db)

    if not new_reply:
        raise HTTPException(status_code=500, detail="Failed to generate reply")

    return AIReplyResponse(**new_reply)
