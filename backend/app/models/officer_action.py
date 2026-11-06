"""
CivicTrack — Officer Action Model (TRD §7.11)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import OfficerActionType


class OfficerAction(Base):
    __tablename__ = "officer_actions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    officer_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    action_type: Mapped[OfficerActionType] = mapped_column(
        Enum(OfficerActionType, native_enum=False, length=40), nullable=False
    )
    directed_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="RESTRICT"), nullable=True
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    complaint = relationship("Complaint")
    officer = relationship("User", foreign_keys=[officer_user_id])
    directed_department = relationship("Department", foreign_keys=[directed_department_id])

    __table_args__ = (
        Index("ix_actions_complaint", "complaint_id", "created_at"),
        Index("ix_actions_officer", "officer_user_id", "created_at"),
    )
