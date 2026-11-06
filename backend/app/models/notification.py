"""`notifications` - owner-scoped in-app notifications (NT-01..NT-08)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

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
    trigger_code: Mapped[str] = mapped_column(String(16), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_notifications_recipient_read", "recipient_user_id", "is_read"),
        Index("ix_notifications_complaint", "complaint_id"),
        Index("ix_notifications_trigger", "trigger_code", "created_at"),
    )
