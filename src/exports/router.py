from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.auth.dependencies import get_current_user
from . import scheduler

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


class ExportScheduleCreateRequest(BaseModel):
    name: str
    export_type: str  # "pdf" or "csv"
    data_source: str  # "contributors", "teams", "trends"
    schedule: str  # daily, weekly, monthly
    recipients: list[str] = []
    config: dict | None = None


class ExportScheduleUpdateRequest(BaseModel):
    name: str | None = None
    export_type: str | None = None
    data_source: str | None = None
    schedule: str | None = None
    recipients: list[str] | None = None
    config: dict | None = None
    is_active: bool | None = None


class ExportScheduleResponse(BaseModel):
    id: str
    name: str
    export_type: str
    data_source: str
    schedule: str
    recipients: list
    config: dict | None
    is_active: bool
    last_run_at: str | None
    next_run_at: str | None
    created_at: str


@router.post(
    "/schedule", response_model=ExportScheduleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_export_schedule(
    body: ExportScheduleCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.schedule not in ("daily", "weekly", "monthly"):
        raise HTTPException(status_code=400, detail="Schedule must be daily, weekly, or monthly")
    if body.export_type not in ("pdf", "csv"):
        raise HTTPException(status_code=400, detail="Export type must be pdf or csv")
    if body.data_source not in ("contributors", "teams", "trends"):
        raise HTTPException(status_code=400, detail="Invalid data source")

    export = await scheduler.create_export(
        db, body.name, body.export_type, body.data_source,
        body.schedule, body.recipients, body.config, user.id,
    )
    return _to_response(export)


@router.get("/schedules", response_model=list[ExportScheduleResponse])
async def list_export_schedules(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exports = await scheduler.list_exports(db, user.id)
    return [_to_response(e) for e in exports]


@router.get("/schedules/{export_id}", response_model=ExportScheduleResponse)
async def get_export_schedule(
    export_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export = await scheduler.get_export(db, export_id, user.id)
    if not export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    return _to_response(export)


@router.put("/schedules/{export_id}", response_model=ExportScheduleResponse)
async def update_export_schedule(
    export_id: str,
    body: ExportScheduleUpdateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export = await scheduler.get_export(db, export_id, user.id)
    if not export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    updates = body.model_dump(exclude_none=True)
    export = await scheduler.update_export(db, export, **updates)
    return _to_response(export)


@router.delete("/schedules/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export_schedule(
    export_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export = await scheduler.get_export(db, export_id, user.id)
    if not export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    await scheduler.delete_export(db, export)


@router.post("/schedules/{export_id}/run")
async def run_export_now(
    export_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    export = await scheduler.get_export(db, export_id, user.id)
    if not export:
        raise HTTPException(status_code=404, detail="Scheduled export not found")
    success = await scheduler.execute_export(export, db)
    return {"status": "success" if success else "failed"}


def _to_response(export) -> ExportScheduleResponse:
    return ExportScheduleResponse(
        id=export.id,
        name=export.name,
        export_type=export.export_type,
        data_source=export.data_source,
        schedule=export.schedule,
        recipients=export.recipients,
        config=export.config,
        is_active=export.is_active,
        last_run_at=export.last_run_at.isoformat() if export.last_run_at else None,
        next_run_at=export.next_run_at.isoformat() if export.next_run_at else None,
        created_at=export.created_at.isoformat(),
    )
