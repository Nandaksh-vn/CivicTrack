"""
CivicTrack — Complaint Category Model (TRD §7.4)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Priority


class ComplaintCategory(Base):
    __tablename__ = "complaint_categories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    default_priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False, length=20), default=Priority.MEDIUM, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    department = relationship("Department")

    __table_args__ = (Index("ix_categories_dept_active", "department_id", "is_active"),)
