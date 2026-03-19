from datetime import datetime

from sqlalchemy import String, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class ScheduledExport(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scheduled_exports"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    export_type: Mapped[str] = mapped_column(String(20), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    schedule: Mapped[str] = mapped_column(String(20), nullable=False)
    recipients: Mapped[list] = mapped_column(JSON, default=list)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )

    created_by_user = relationship("User", back_populates="scheduled_exports")
