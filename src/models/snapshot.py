from sqlalchemy import String, Integer, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class Snapshot(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "snapshots"

    snapshot_date: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    repo_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False)
    commit_count: Mapped[int] = mapped_column(Integer, default=0)
    pr_count: Mapped[int] = mapped_column(Integer, default=0)
    open_issues: Mapped[int] = mapped_column(Integer, default=0)
    closed_issues: Mapped[int] = mapped_column(Integer, default=0)
    security_alerts: Mapped[int] = mapped_column(Integer, default=0)
    contributors_count: Mapped[int] = mapped_column(Integer, default=0)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
