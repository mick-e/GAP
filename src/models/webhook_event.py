from sqlalchemy import String, JSON, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class WebhookEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "webhook_events"

    event_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    action: Mapped[str | None] = mapped_column(String(50), nullable=True)
    repo_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    sender: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    delivery_id: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
