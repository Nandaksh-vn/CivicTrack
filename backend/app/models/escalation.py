"""
CivicTrack — Escalation Model (TRD §7.10)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Status, TriggerSource


class Escalation(Base):
    __tablename__ = "escalations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), unique=True, nullable=False
    )
    escalation_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    previous_status: Mapped[Status] = mapped_column(
        Enum(Status, native_enum=False, length=40), nullable=False
    )
    deadline_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    escalated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    overdue_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger_source: Mapped[TriggerSource] = mapped_column(
        Enum(TriggerSource, native_enum=False, length=40), nullable=False
    )
    reason_code: Mapped[str] = mapped_column(String(40), default="SLA_BREACH", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    complaint = relationship("Complaint")

    __table_args__ = (
        Index("ix_escalation_escalated_at", "escalated_at"),
        Index("ix_escalation_trigger_source", "trigger_source"),
    )
