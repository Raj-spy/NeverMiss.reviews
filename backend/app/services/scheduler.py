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

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def check_all_businesses():
    """
    Scheduled task: Iterates all registered businesses and scrapes for new reviews.
    """
    print(f"[Scheduler] Running review check at {datetime.utcnow().isoformat()}")

    db = get_supabase()

    # Fetch all businesses
    res = db.table("businesses").select("id, business_name, google_maps_url").execute()
    businesses = res.data or []

    print(f"[Scheduler] Checking {len(businesses)} businesses")

    for business in businesses:
        try:
            new_ids = await scrape_reviews_for_business(
                business["id"],
                business["google_maps_url"],
                db,
            )

            if new_ids:
                print(f"[Scheduler] {len(new_ids)} new reviews for '{business['business_name']}'")

                await generate_replies_for_business(new_ids, db)

            else:
                print(f"[Scheduler] No new reviews for '{business['business_name']}'")

        except Exception as e:
            print(f"[Scheduler] Error processing business {business['id']}: {e}")

    print("[Scheduler] Review check complete")


def start_scheduler():
    """
    Starts scheduler on FastAPI startup
    """

    # FOR DEVELOPMENT (every 1 minute)
    scheduler.add_job(
        check_all_businesses,
        trigger=IntervalTrigger(minutes=1),
        id="review_checker",
        name="Review Checker Dev Mode",
        replace_existing=True,
    )

    scheduler.start()

    print("[Scheduler] Started — checking every 1 minute (DEV MODE)")


def stop_scheduler():
    """
    Stop scheduler when server shuts down
    """
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")