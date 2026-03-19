from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.auth.dependencies import get_current_user
from src.audit.service import log_action
from . import service
from .executor import execute_scheduled_job
from .templates import SCHEDULE_TEMPLATES

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


class ScheduleTemplate(BaseModel):
    id: str
    name: str
    description: str
    report_type: str
    schedule: str
    config: dict


class ScheduleFromTemplateRequest(BaseModel):
    template_id: str
    recipients: list[str] = []
    name: str | None = None


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    request: Request,
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
    await log_action(
        db, user.id, "schedule.create", "schedule", job.id,
        details={"name": body.name, "report_type": body.report_type},
        ip_address=request.client.host if request.client else None,
    )
    return _to_response(job)


@router.get("", response_model=list[ScheduleResponse])
async def list_schedules(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    jobs = await service.list_jobs(db, user.id)
    return [_to_response(j) for j in jobs]


# Template routes must come before /{schedule_id} to avoid path conflicts
@router.get("/templates", response_model=list[ScheduleTemplate])
async def list_templates():
    return [
        ScheduleTemplate(id=tid, **tpl)
        for tid, tpl in SCHEDULE_TEMPLATES.items()
    ]


@router.get("/templates/{template_id}", response_model=ScheduleTemplate)
async def get_template(template_id: str):
    tpl = SCHEDULE_TEMPLATES.get(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return ScheduleTemplate(id=template_id, **tpl)


@router.post(
    "/from-template", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED
)
async def create_from_template(
    body: ScheduleFromTemplateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tpl = SCHEDULE_TEMPLATES.get(body.template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")

    name = body.name or tpl["name"]
    job = await service.create_job(
        db,
        name,
        tpl["report_type"],
        tpl["schedule"],
        body.recipients,
        tpl["config"],
        user.id,
    )
    return _to_response(job)


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
    request: Request,
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
    await log_action(
        db, user.id, "schedule.update", "schedule", schedule_id,
        details=updates,
        ip_address=request.client.host if request.client else None,
    )
    return _to_response(job)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    request: Request,
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await service.delete_job(db, job)
    await log_action(
        db, user.id, "schedule.delete", "schedule", schedule_id,
        ip_address=request.client.host if request.client else None,
    )


@router.post("/{schedule_id}/run")
async def run_schedule(
    request: Request,
    schedule_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await service.get_job(db, schedule_id, user.id)
    if not job:
        raise HTTPException(status_code=404, detail="Schedule not found")
    success = await execute_scheduled_job(job, db)
    await log_action(
        db, user.id, "schedule.run", "schedule", schedule_id,
        details={"report_type": job.report_type},
        status="success" if success else "failure",
        ip_address=request.client.host if request.client else None,
    )
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
