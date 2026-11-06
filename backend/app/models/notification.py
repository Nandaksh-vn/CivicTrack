"""
CivicTrack — Notification Model (TRD §7.9)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    complaint_id: Mapped[int | None] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=True
    )
    trigger_code: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_user_id])
    complaint = relationship("Complaint", foreign_keys=[complaint_id])

    __table_args__ = (
        Index("ix_notifications_user_read", "recipient_user_id", "is_read", "created_at"),
        Index("ix_notifications_complaint", "complaint_id", "created_at"),
    )
