from sqlalchemy import String, Float, Integer, JSON, Date
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class TeamMetrics(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "team_metrics"

    metrics_date: Mapped[str] = mapped_column(Date, nullable=False, index=True)
    repo_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    deployment_frequency: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_hours: Mapped[float] = mapped_column(Float, default=0.0)
    mttr_hours: Mapped[float] = mapped_column(Float, default=0.0)
    change_failure_rate: Mapped[float] = mapped_column(Float, default=0.0)
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    total_prs: Mapped[int] = mapped_column(Integer, default=0)
    total_releases: Mapped[int] = mapped_column(Integer, default=0)
    contributors_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
