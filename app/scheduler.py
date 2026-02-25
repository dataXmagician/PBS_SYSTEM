"""
APScheduler Setup - DWH Transfer Zamanlama

AsyncIOScheduler + SQLAlchemyJobStore ile PostgreSQL'de persist eden
zamanlama altyapisi. FastAPI lifecycle event'leriyle entegre.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: AsyncIOScheduler = None


def init_scheduler() -> AsyncIOScheduler:
    """
    APScheduler'i baslat.
    SQLAlchemyJobStore ile PostgreSQL'de job'lar persist edilir.
    """
    global scheduler

    jobstores = {
        'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
    }

    executors = {
        'default': ThreadPoolExecutor(max_workers=5)
    }

    job_defaults = {
        'coalesce': True,       # Kacirilan job'lari birlestir
        'max_instances': 1,     # Ayni job'u paralel calistirma
        'misfire_grace_time': 300  # 5 dk tolerans
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='Europe/Istanbul'
    )

    return scheduler


def start_scheduler():
    """Scheduler'i baslat."""
    global scheduler
    if scheduler and not scheduler.running:
        scheduler.start()
        logger.info("APScheduler baslatildi.")


def shutdown_scheduler():
    """Scheduler'i durdur."""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("APScheduler durduruldu.")


def get_scheduler() -> AsyncIOScheduler:
    """Global scheduler instance'i dondur."""
    global scheduler
    return scheduler
