from datetime import datetime
from pydantic import BaseModel


class AuditLogEntry(BaseModel):
    id: str
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    details: dict | None
    ip_address: str | None
    status: str
    created_at: str


class AuditLogFilter(BaseModel):
    action: str | None = None
    user_id: str | None = None
    resource_type: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    limit: int = 50
    offset: int = 0


class AuditStats(BaseModel):
    total: int
    by_action: dict[str, int]
    by_day: dict[str, int]
