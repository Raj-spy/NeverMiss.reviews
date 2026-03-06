# backend/app/core/config.py
# Central configuration using pydantic-settings for env var validation

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "AI Review Manager"
    environment: str = "development"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_service_key: str
    database_url: str

    # JWT
    secret_key: str
    access_token_expire_minutes: int = 60

    # groq
    groq_api_key: str
    # Apify
    apify_api_token: str

    # Scheduler
    review_check_interval_hours: int = 6

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()
