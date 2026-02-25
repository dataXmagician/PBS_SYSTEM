"""
DWH Schedule Service - Transfer Zamanlama Servisi

APScheduler ile DWH transfer zamanlamalarini yonetir.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from app.models.dwh import DwhSchedule, DwhTransfer, DwhScheduleFrequency
from app.scheduler import get_scheduler
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

# Job ID pattern
JOB_ID_PREFIX = "dwh_transfer_"


def _make_job_id(transfer_id: int) -> str:
    return f"{JOB_ID_PREFIX}{transfer_id}"


def execute_scheduled_transfer(transfer_id: int):
    """
    APScheduler callback.
    Yeni DB session acar, transfer'i yukler ve calistirir.
    """
    from app.services.dwh_transfer_service import DwhTransferService
    from sqlalchemy.orm import joinedload

    logger.info(f"Zamanlanmis transfer baslatiliyor: transfer_id={transfer_id}")

    db = SessionLocal()
    try:
        transfer = db.query(DwhTransfer)\
            .options(
                joinedload(DwhTransfer.dwh_table),
                joinedload(DwhTransfer.source_query)
            )\
            .filter(DwhTransfer.id == transfer_id)\
            .first()

        if not transfer:
            logger.error(f"Transfer bulunamadi: {transfer_id}")
            return

        if not transfer.is_active:
            logger.info(f"Transfer pasif, atlanıyor: {transfer_id}")
            return

        # Transfer calistir
        log = DwhTransferService.execute_transfer(db, transfer, triggered_by="scheduler")

        # Schedule'in last_run_at guncelle
        schedule = transfer.schedule
        if schedule:
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = calculate_next_run(schedule)
            db.commit()

        logger.info(
            f"Zamanlanmis transfer tamamlandi: transfer_id={transfer_id}, "
            f"status={log.status}"
        )

    except Exception as e:
        logger.error(f"Zamanlanmis transfer hatasi: transfer_id={transfer_id}, hata={e}")
    finally:
        db.close()


def register_schedule(schedule: DwhSchedule) -> bool:
    """
    DwhSchedule -> APScheduler job olustur.
    Mevcut job varsa gunceller.
    """
    sched = get_scheduler()
    if not sched:
        logger.warning("Scheduler baslatilmamis, zamanlama kaydedilemedi.")
        return False

    job_id = _make_job_id(schedule.transfer_id)
    trigger = _build_trigger(schedule)

    if trigger is None:
        logger.info(f"Manual zamanlama, APScheduler job olusturulmuyor: {job_id}")
        # Mevcut job varsa kaldir
        try:
            sched.remove_job(job_id)
        except Exception:
            pass
        return True

    # Job ekle/guncelle
    try:
        existing = sched.get_job(job_id)
        if existing:
            existing.reschedule(trigger=trigger)
            logger.info(f"APScheduler job guncellendi: {job_id}")
        else:
            sched.add_job(
                execute_scheduled_transfer,
                trigger=trigger,
                id=job_id,
                args=[schedule.transfer_id],
                replace_existing=True,
                name=f"DWH Transfer #{schedule.transfer_id}"
            )
            logger.info(f"APScheduler job olusturuldu: {job_id}")
        return True

    except Exception as e:
        logger.error(f"APScheduler job hatasi: {job_id}, hata={e}")
        return False


def unregister_schedule(transfer_id: int) -> bool:
    """APScheduler job sil."""
    sched = get_scheduler()
    if not sched:
        return False

    job_id = _make_job_id(transfer_id)
    try:
        sched.remove_job(job_id)
        logger.info(f"APScheduler job silindi: {job_id}")
        return True
    except Exception:
        return False


def load_all_schedules(db: Session):
    """
    Startup'ta tum aktif schedule'lari APScheduler'a kaydet.
    """
    schedules = db.query(DwhSchedule).filter(
        DwhSchedule.is_enabled == True
    ).all()

    count = 0
    for schedule in schedules:
        freq = schedule.frequency
        if hasattr(freq, 'value'):
            freq = freq.value
        if freq != "manual":
            if register_schedule(schedule):
                count += 1

    logger.info(f"Startup: {count} zamanlama APScheduler'a yuklendi.")


def calculate_next_run(schedule: DwhSchedule) -> Optional[datetime]:
    """Zamanlama ayarlarina gore next_run_at hesapla."""
    freq = schedule.frequency
    if hasattr(freq, 'value'):
        freq = freq.value

    now = datetime.utcnow()

    if freq == "manual":
        return None
    elif freq == "hourly":
        return now + timedelta(hours=1)
    elif freq == "daily":
        # Bugunku veya yarin saat:dakika
        hour = schedule.hour or 0
        minute = schedule.minute or 0
        next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_time <= now:
            next_time += timedelta(days=1)
        return next_time
    elif freq == "weekly":
        hour = schedule.hour or 0
        minute = schedule.minute or 0
        target_dow = schedule.day_of_week or 0  # 0=Pazartesi
        days_ahead = target_dow - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_time = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=minute, second=0, microsecond=0
        )
        return next_time
    elif freq == "monthly":
        hour = schedule.hour or 0
        minute = schedule.minute or 0
        dom = schedule.day_of_month or 1
        # Bu ayin veya gelecek ayin target gunu
        try:
            next_time = now.replace(day=dom, hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            # Ay sonunu asan gun (orn: 31. gun)
            next_time = now.replace(day=28, hour=hour, minute=minute, second=0, microsecond=0)
        if next_time <= now:
            # Gelecek ay
            if now.month == 12:
                next_time = next_time.replace(year=now.year + 1, month=1)
            else:
                next_time = next_time.replace(month=now.month + 1)
        return next_time
    elif freq == "cron":
        # Cron icin APScheduler kendi hesaplar, yaklaşık 1 saat sonra ver
        return now + timedelta(hours=1)

    return None


def _build_trigger(schedule: DwhSchedule):
    """DwhSchedule'dan APScheduler trigger olustur."""
    freq = schedule.frequency
    if hasattr(freq, 'value'):
        freq = freq.value

    if freq == "manual":
        return None
    elif freq == "hourly":
        return IntervalTrigger(hours=1)
    elif freq == "daily":
        return CronTrigger(
            hour=schedule.hour or 0,
            minute=schedule.minute or 0
        )
    elif freq == "weekly":
        return CronTrigger(
            day_of_week=schedule.day_of_week or 0,
            hour=schedule.hour or 0,
            minute=schedule.minute or 0
        )
    elif freq == "monthly":
        return CronTrigger(
            day=schedule.day_of_month or 1,
            hour=schedule.hour or 0,
            minute=schedule.minute or 0
        )
    elif freq == "cron":
        if schedule.cron_expression:
            parts = schedule.cron_expression.strip().split()
            if len(parts) == 5:
                return CronTrigger(
                    minute=parts[0],
                    hour=parts[1],
                    day=parts[2],
                    month=parts[3],
                    day_of_week=parts[4]
                )
        # Fallback
        return CronTrigger(hour=0, minute=0)

    return None
