# backend/app/core/database.py
# Supabase client setup — used across all services for DB operations

from supabase import create_client, Client
from .config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_supabase() -> Client:
    """
    Returns a cached Supabase client using the service role key.
    Service role bypasses Row Level Security for backend operations.
    """
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_supabase_client() -> Client:
    """Dependency injection version for FastAPI routes."""
    return get_supabase()
