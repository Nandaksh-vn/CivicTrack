"""`officer_actions` - append-only superintendent decision log."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

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
    directed_department_id: Mapped[int | None] = mapped_column(
        ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )
    action_type: Mapped[OfficerActionType] = mapped_column(
        Enum(OfficerActionType, native_enum=False, length=40), nullable=False
    )
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (
        Index("ix_officer_actions_complaint_created", "complaint_id", "created_at"),
        Index("ix_officer_actions_officer", "officer_user_id", "created_at"),
    )
