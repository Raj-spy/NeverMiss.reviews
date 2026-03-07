# backend/app/services/scheduler.py
# APScheduler background job that periodically checks all businesses for new reviews

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from ..core.config import get_settings
from ..core.database import get_supabase
from .apify_service import scrape_reviews_for_business
from .ai_service import generate_replies_for_business

settings = get_settings()

scheduler = AsyncIOScheduler()


async def check_all_businesses():
    """
    Scheduled task: Iterates all businesses and does incremental scrape.
    Only fetches latest 20 reviews per business — is_initial=False.
    """
    print(f"[Scheduler] Running review check at {datetime.utcnow().isoformat()}")

    db = get_supabase()

    res = db.table("businesses").select(
        "id, business_name, google_maps_url, last_scraped_at"
    ).execute()
    businesses = res.data or []

    print(f"[Scheduler] Checking {len(businesses)} businesses")

    for business in businesses:
        try:
            # Skip businesses that were scraped in the last 30 minutes
            # Prevents duplicate runs if scheduler overlaps
            last_scraped = business.get("last_scraped_at")
            if last_scraped:
                from datetime import timezone
                last_scraped_dt = datetime.fromisoformat(
                    last_scraped.replace("Z", "+00:00")
                )
                now = datetime.now(timezone.utc)
                minutes_since = (now - last_scraped_dt).total_seconds() / 60
                if minutes_since < 30:
                    print(
                        f"[Scheduler] Skipping '{business['business_name']}' "
                        f"— scraped {int(minutes_since)}m ago"
                    )
                    continue

            # Incremental scrape — only latest 20 reviews
            new_ids = await scrape_reviews_for_business(
                business["id"],
                business["google_maps_url"],
                db,
                is_initial=False,      # ← incremental only
            )

            if new_ids:
                print(
                    f"[Scheduler] {len(new_ids)} new reviews "
                    f"for '{business['business_name']}'"
                )
                await generate_replies_for_business(new_ids, db)
            else:
                print(f"[Scheduler] No new reviews for '{business['business_name']}'")

        except Exception as e:
            print(f"[Scheduler] Error processing '{business['business_name']}': {e}")

    print("[Scheduler] Review check complete")


def start_scheduler():
    """
    Starts the scheduler on FastAPI startup.

    DEV MODE  — every 6 hours (change minutes=1 to hours=6 for production)
    PROD MODE — every 6 hours
    """
    is_dev = settings.environment == "development"

    if is_dev:
        # Dev — every 6 hours but can manually trigger via /business/{id}/refresh
        scheduler.add_job(
            check_all_businesses,
            trigger=IntervalTrigger(hours=6),
            id="review_checker",
            name="Review Checker",
            replace_existing=True,
        )
        print("[Scheduler] Started — checking every 6 hours")
    else:
        # Production — every 6 hours
        scheduler.add_job(
            check_all_businesses,
            trigger=IntervalTrigger(hours=6),
            id="review_checker",
            name="Review Checker",
            replace_existing=True,
        )
        print("[Scheduler] Started — checking every 6 hours (PRODUCTION)")

    scheduler.start()


def stop_scheduler():
    """Stop scheduler on server shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")