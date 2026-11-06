"""
CivicTrack — Complaint Model (TRD §7.5)
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Priority, Status


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    citizen_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("complaint_categories.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location_text: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 6), nullable=True)
    status: Mapped[Status] = mapped_column(
        Enum(Status, native_enum=False, length=40),
        default=Status.SUBMITTED,
        nullable=False,
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, native_enum=False, length=20),
        default=Priority.MEDIUM,
        nullable=False,
    )
    assigned_to_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accepted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    sla_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    resolution_due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    resolved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    rejected_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reopened_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    citizen = relationship("User", foreign_keys=[citizen_id])
    department = relationship("Department", foreign_keys=[department_id])
    category = relationship("ComplaintCategory", foreign_keys=[category_id])

    __table_args__ = (
        Index("ix_complaints_dept_status_sub", "department_id", "status", "submitted_at"),
        Index("ix_complaints_citizen_sub", "citizen_id", "submitted_at"),
        Index("ix_complaints_status_due", "status", "resolution_due_at"),
        CheckConstraint(
            "(latitude IS NULL) = (longitude IS NULL)",
            name="ck_complaints_coordinates_paired",
        ),
        CheckConstraint(
            "latitude BETWEEN -90 AND 90 OR latitude IS NULL",
            name="ck_complaints_latitude_range",
        ),
        CheckConstraint(
            "longitude BETWEEN -180 AND 180 OR longitude IS NULL",
            name="ck_complaints_longitude_range",
        ),
        CheckConstraint(
            "resolution_due_at IS NULL OR accepted_at IS NOT NULL",
            name="ck_complaints_deadline_requires_acceptance",
        ),
    )
