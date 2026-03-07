# backend/app/models/schemas.py
# Pydantic schemas for request/response validation across all API routes

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Auth ────────────────────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str


# ─── Business ────────────────────────────────────────────────────────────────

class BusinessCreate(BaseModel):
    business_name: str = Field(min_length=1, max_length=255)
    google_maps_url: str = Field(min_length=10)
    description: Optional[str] = None

class BusinessResponse(BaseModel):
    id: str
    user_id: str
    business_name: str
    google_maps_url: str
    description: Optional[str]
    created_at: datetime
    review_count: Optional[int] = 0
    avg_rating: Optional[float] = None
    last_scraped_at: Optional[datetime] = None      # naya
    total_reviews_scraped: Optional[int] = 0        # naya


# ─── Reviews ─────────────────────────────────────────────────────────────────

class ReviewResponse(BaseModel):
    id: str
    business_id: str
    reviewer_name: Optional[str]
    review_text: str
    rating: int
    review_date: Optional[str]
    created_at: datetime
    processed: bool
    business_name: Optional[str] = None


class ReviewWithReply(ReviewResponse):
    reply: Optional["AIReplyResponse"] = None


# ─── AI Replies ───────────────────────────────────────────────────────────────

class ReplyStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class AIReplyResponse(BaseModel):
    id: str
    review_id: str
    reply_text: str
    status: ReplyStatus
    created_at: datetime
    updated_at: Optional[datetime]


class ApproveReplyRequest(BaseModel):
    reply_id: str
    edited_text: Optional[str] = None  # If provided, update the reply text before approving


class RejectReplyRequest(BaseModel):
    reply_id: str


# ─── Analytics ───────────────────────────────────────────────────────────────

class AnalyticsSummary(BaseModel):
    total_reviews: int
    avg_rating: float
    pending_replies: int
    approved_replies: int
    reviews_this_week: int
    rating_distribution: dict  # {1: count, 2: count, ...}


# ─── Generic ─────────────────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# Forward reference resolution
ReviewWithReply.model_rebuild()
