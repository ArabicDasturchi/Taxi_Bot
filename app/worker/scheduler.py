import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.worker.scraper import send_ads_to_groups

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()

def start_scheduler():
    logger.info("Scheduling auto ad tasks every 5 minutes...")
    scheduler.add_job(send_ads_to_groups, "interval", minutes=5)
    scheduler.start()
