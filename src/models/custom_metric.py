from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class CustomMetric(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "custom_metrics"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    formula: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by_user = relationship("User", back_populates="custom_metrics")
