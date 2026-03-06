# backend/app/api/auth.py
# Authentication routes: signup and login

from fastapi import APIRouter, HTTPException, status, Depends
from supabase import Client
import uuid

from ..models.schemas import SignupRequest, LoginRequest, TokenResponse, MessageResponse
from ..core.security import hash_password, verify_password, create_access_token
from ..core.database import get_supabase_client

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Client = Depends(get_supabase_client)):
    """
    Register a new user.
    Checks for duplicate email, hashes password, stores in Supabase.
    """
    # Check if email already exists
    existing = db.table("users").select("id").eq("email", payload.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_id = str(uuid.uuid4())
    db.table("users").insert({
        "id": user_id,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "full_name": payload.full_name or "",
    }).execute()

    return MessageResponse(message="Account created successfully")


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Client = Depends(get_supabase_client)):
    """
    Authenticate user and return JWT token.
    """
    result = db.table("users").select("*").eq("email", payload.email).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    user = result.data[0]

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token({"sub": user["id"], "email": user["email"]})

    return TokenResponse(
        access_token=token,
        user_id=user["id"],
        email=user["email"],
    )
