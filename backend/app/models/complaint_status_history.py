"""`complaint_status_history` - append-only status transition log."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import Status


class ComplaintStatusHistory(Base):
    __tablename__ = "complaint_status_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    from_status: Mapped[Status | None] = mapped_column(
        Enum(Status, native_enum=False, length=40), nullable=True
    )
    to_status: Mapped[Status] = mapped_column(
        Enum(Status, native_enum=False, length=40), nullable=False
    )
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=True
    )
    actor_role: Mapped[str] = mapped_column(String(40), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (Index("ix_status_history_complaint_created", "complaint_id", "created_at"),)
