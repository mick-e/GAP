import logging
from datetime import datetime, timezone

from sqlalchemy import select, func, String
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.audit_log import AuditLog
from .schemas import AuditLogFilter

logger = logging.getLogger(__name__)


async def log_action(
    db: AsyncSession,
    user_id: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    status: str = "success",
) -> AuditLog:
    """Create an audit log entry. Does not commit — caller manages transaction."""
    try:
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
        db.add(entry)
        await db.flush()
        logger.info(
            "Audit: %s user=%s resource=%s/%s status=%s",
            action, user_id, resource_type, resource_id, status,
        )
        return entry
    except Exception:
        logger.warning(
            "Failed to create audit log: %s user=%s", action, user_id, exc_info=True
        )
        return None


async def get_audit_logs(
    db: AsyncSession, filters: AuditLogFilter
) -> list[AuditLog]:
    """Query audit logs with filtering and pagination."""
    query = select(AuditLog)

    if filters.action:
        query = query.where(AuditLog.action == filters.action)
    if filters.user_id:
        query = query.where(AuditLog.user_id == filters.user_id)
    if filters.resource_type:
        query = query.where(AuditLog.resource_type == filters.resource_type)
    if filters.status:
        query = query.where(AuditLog.status == filters.status)
    if filters.start_date:
        query = query.where(AuditLog.created_at >= filters.start_date)
    if filters.end_date:
        query = query.where(AuditLog.created_at <= filters.end_date)

    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset(filters.offset).limit(filters.limit)

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_user_audit_trail(
    db: AsyncSession, user_id: str, limit: int = 50
) -> list[AuditLog]:
    """Get audit trail for a specific user."""
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_audit_stats(db: AsyncSession) -> dict:
    """Get audit log statistics: counts by action and by day."""
    # Total count
    total_result = await db.execute(select(func.count(AuditLog.id)))
    total = total_result.scalar() or 0

    # Counts by action
    action_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
    )
    by_action = {row[0]: row[1] for row in action_result.all()}

    # Counts by day (use substr for SQLite compatibility)
    day_expr = func.substr(func.cast(AuditLog.created_at, String), 1, 10)
    day_result = await db.execute(
        select(day_expr.label("day"), func.count(AuditLog.id))
        .group_by(day_expr)
        .order_by(day_expr)
    )
    by_day = {str(row[0]): row[1] for row in day_result.all()}

    return {"total": total, "by_action": by_action, "by_day": by_day}
