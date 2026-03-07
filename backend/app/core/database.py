# backend/app/core/database.py
# Supabase client setup — used across all services for DB operations

from supabase import create_client, Client
from .config import get_settings


def get_supabase() -> Client:
    """
    Creates a fresh Supabase client per call using the service role key.
    
    No @lru_cache — avoids reusing stale HTTP/2 connections that cause
    RemoteProtocolError when Supabase closes idle connections.
    """
    settings = get_settings()  # this is still cached/fast via lru_cache in config.py
    return create_client(settings.supabase_url, settings.supabase_service_key)


def get_supabase_client() -> Client:
    """Dependency injection version for FastAPI routes."""
    return get_supabase()