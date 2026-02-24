import asyncio
import logging
from datetime import datetime, timedelta, timezone

from src.database import get_session_factory
from .service import get_due_jobs, SCHEDULE_INTERVALS
from .executor import execute_scheduled_job

logger = logging.getLogger(__name__)

_task: asyncio.Task | None = None
_running = False


async def _scheduler_loop():
    global _running
    _running = True
    logger.info("Background scheduler started")
    while _running:
        try:
            session_factory = get_session_factory()
            async with session_factory() as db:
                due_jobs = await get_due_jobs(db)
                for job in due_jobs:
                    try:
                        success = await execute_scheduled_job(job, db)
                        if success:
                            interval = SCHEDULE_INTERVALS.get(job.schedule, timedelta(days=1))
                            job.next_run_at = datetime.now(timezone.utc) + interval
                            await db.commit()
                            logger.info(f"Scheduled job '{job.name}' executed, next run: {job.next_run_at}")
                        else:
                            logger.warning(f"Scheduled job '{job.name}' failed")
                    except Exception as e:
                        logger.error(f"Error executing job '{job.name}': {e}")
        except Exception as e:
            logger.error(f"Scheduler loop error: {e}")
        await asyncio.sleep(60)


async def start_scheduler():
    global _task
    if _task is not None:
        return
    _task = asyncio.create_task(_scheduler_loop())
    logger.info("Scheduler task created")


async def stop_scheduler():
    global _task, _running
    _running = False
    if _task is not None:
        _task.cancel()
        try:
            await _task
        except asyncio.CancelledError:
            pass
        _task = None
    logger.info("Scheduler stopped")
