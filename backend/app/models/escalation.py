"""`escalations` - exactly one row per complaint that missed its deadline."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Status, TriggerSource


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    escalation_number: Mapped[str | None] = mapped_column(String(32), unique=True, nullable=True)
    previous_status: Mapped[Status] = mapped_column(
        Enum(Status, native_enum=False, length=40), nullable=False
    )
    deadline_at: Mapped[datetime] = mapped_column(nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    overdue_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    trigger_source: Mapped[TriggerSource] = mapped_column(
        Enum(TriggerSource, native_enum=False, length=40), nullable=False
    )
    reason_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("overdue_seconds >= 0", name="ck_escalations_overdue_nonnegative"),
        Index("ix_escalations_deadline", "deadline_at"),
    )
