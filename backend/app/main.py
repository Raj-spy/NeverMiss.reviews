# backend/app/main.py
# FastAPI application entry point — registers routes, middleware, and lifecycle events

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import get_settings
from .api import auth, business, reviews, replies
from .services.scheduler import start_scheduler, stop_scheduler

settings = get_settings()

# ─── App Initialization ───────────────────────────────────────────────────────

app = FastAPI(
    title="AI Review Manager API",
    description="Multi-tenant SaaS for Google review monitoring and AI reply generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS Middleware ──────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── API Routes ───────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(business.router)
app.include_router(reviews.router)
app.include_router(replies.router)

# ─── Lifecycle Events ─────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    """Start background scheduler when the app launches."""
    print("[App] Starting AI Review Manager API")
    start_scheduler()


@app.on_event("shutdown")
async def on_shutdown():
    """Gracefully stop the scheduler on shutdown."""
    stop_scheduler()
    print("[App] Shutdown complete")


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.app_name,
        "environment": settings.environment,
    }
