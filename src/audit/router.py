from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_db
from src.models.user import User
from src.auth.dependencies import require_admin
from .schemas import AuditLogEntry, AuditLogFilter, AuditStats
from . import service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


def _to_response(entry) -> AuditLogEntry:
    return AuditLogEntry(
        id=entry.id,
        user_id=entry.user_id,
        action=entry.action,
        resource_type=entry.resource_type,
        resource_id=entry.resource_id,
        details=entry.details,
        ip_address=entry.ip_address,
        status=entry.status,
        created_at=entry.created_at.isoformat(),
    )


@router.get("/logs", response_model=list[AuditLogEntry])
async def list_audit_logs(
    action: str | None = Query(None),
    user_id: str | None = Query(None),
    resource_type: str | None = Query(None),
    status: str | None = Query(None),
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    filters = AuditLogFilter(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        status=status,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    logs = await service.get_audit_logs(db, filters)
    return [_to_response(entry) for entry in logs]


@router.get("/logs/{user_id}", response_model=list[AuditLogEntry])
async def get_user_audit_trail(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    logs = await service.get_user_audit_trail(db, user_id, limit)
    return [_to_response(entry) for entry in logs]


@router.get("/stats", response_model=AuditStats)
async def audit_stats(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    return await service.get_audit_stats(db)
