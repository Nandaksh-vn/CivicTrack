"""
CivicTrack — User Model (TRD §7.2)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(190), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role: Mapped[Role] = mapped_column(
        Enum(Role, native_enum=False, length=40), nullable=False, default=Role.CITIZEN
    )
    department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    department = relationship("Department", back_populates="users")

    __table_args__ = (
        Index("ix_users_role_active", "role", "is_active"),
        Index("ix_users_dept_role", "department_id", "role"),
    )
