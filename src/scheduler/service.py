from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.scheduled_job import ScheduledJob

SCHEDULE_INTERVALS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
    "monthly": timedelta(days=30),
}


async def create_job(
    db: AsyncSession,
    name: str,
    report_type: str,
    schedule: str,
    recipients: list[str],
    config: dict,
    user_id: str,
) -> ScheduledJob:
    interval = SCHEDULE_INTERVALS.get(schedule, timedelta(days=1))
    job = ScheduledJob(
        name=name,
        report_type=report_type,
        schedule=schedule,
        recipients=recipients,
        config=config,
        created_by=user_id,
        next_run_at=datetime.now(timezone.utc) + interval,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def list_jobs(db: AsyncSession, user_id: str) -> list[ScheduledJob]:
    result = await db.execute(
        select(ScheduledJob).where(ScheduledJob.created_by == user_id)
    )
    return list(result.scalars().all())


async def get_job(db: AsyncSession, job_id: str, user_id: str) -> ScheduledJob | None:
    result = await db.execute(
        select(ScheduledJob).where(
            ScheduledJob.id == job_id, ScheduledJob.created_by == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_job(
    db: AsyncSession, job: ScheduledJob, **kwargs
) -> ScheduledJob:
    for key, value in kwargs.items():
        if hasattr(job, key):
            setattr(job, key, value)
    if "schedule" in kwargs:
        interval = SCHEDULE_INTERVALS.get(kwargs["schedule"], timedelta(days=1))
        job.next_run_at = datetime.now(timezone.utc) + interval
    await db.commit()
    await db.refresh(job)
    return job


async def delete_job(db: AsyncSession, job: ScheduledJob) -> None:
    await db.delete(job)
    await db.commit()


async def get_due_jobs(db: AsyncSession) -> list[ScheduledJob]:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(ScheduledJob).where(
            ScheduledJob.is_active.is_(True),
            ScheduledJob.next_run_at <= now,
        )
    )
    return list(result.scalars().all())
