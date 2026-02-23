from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.auth.dependencies import get_current_user
from . import service
from .executor import execute_scheduled_job

router = APIRouter(prefix="/api/v1/schedules", tags=["schedules"])


class ScheduleCreateRequest(BaseModel):
    name: str
    report_type: str
    schedule: str  # daily, weekly, monthly
    recipients: list[str] = []
    config: dict = {}


class ScheduleUpdateRequest(BaseModel):
    name: str | None = None
    schedule: str | None = None
    recipients: list[str] | None = None
    config: dict | None = None
    is_active: bool | None = None


class ScheduleResponse(BaseModel):
    id: str
    name: str
    report_type: str
    schedule: str
    recipients: list
    config: dict
    is_active: bool
    last_run_at: str | None
    next_run_at: str | None
    created_at: str


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    body: ScheduleCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.schedule not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Schedule must be daily, weekly, or monthly")
    if body.report_type not in ("activity", "quality", "releases"):
        raise HTTPException(status_code=400, detail="Invalid report type")

    job = await service.create_job(
        db, body.name, body.report_type, body.schedule, body.recipients, body.config, user.id
    )
    return _to_response(job)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    jobs = await service.list_jobs(db, user.id)
    return [_to_response(j) for j in jobs]


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return _to_response(job)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: str,
    body: ScheduleUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")

    updates = body.model_dump(exclude_none=True)
    job = await service.update_job(db, job, **updates)
    return _to_response(job)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await service.delete_job(db, job)


@router.post("/{schedule_id}/run")
async def run_schedule(
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    success = await execute_scheduled_job(job, db)
    return {"status": "success" if success else "failed"}


def _to_response(job) -> ScheduleResponse:
    return ScheduleResponse(
        id=job.id,
        name=job.name,
        report_type=job.report_type,
        schedule=job.schedule,
        recipients=job.recipients,
        config=job.config,
        is_active=job.is_active,
        last_run_at=job.last_run_at.isoformat() if job.last_run_at else None,
        next_run_at=job.next_run_at.isoformat() if job.next_run_at else None,
        created_at=job.created_at.isoformat(),
    )
