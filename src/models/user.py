from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from .base import UUIDMixin, TimestampMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(50), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="created_by_user", cascade="all, delete-orphan")
    scheduled_jobs = relationship(
        "ScheduledJob", back_populates="created_by_user", cascade="all, delete-orphan"
    )
