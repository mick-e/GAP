from sqlalchemy import String, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class Contributor(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contributors"

    login: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    html_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_commits: Mapped[int] = mapped_column(Integer, default=0)
    total_prs: Mapped[int] = mapped_column(Integer, default=0)
    total_issues: Mapped[int] = mapped_column(Integer, default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    lines_added: Mapped[int] = mapped_column(Integer, default=0)
    lines_removed: Mapped[int] = mapped_column(Integer, default=0)
    repos: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
