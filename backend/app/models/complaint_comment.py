"""`complaint_comments` - citizen-visible and internal progress notes."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import CommentType, CommentVisibility


class ComplaintComment(Base):
    __tablename__ = "complaint_comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    author_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    comment_type: Mapped[CommentType] = mapped_column(
        Enum(CommentType, native_enum=False, length=40), nullable=False
    )
    visibility: Mapped[CommentVisibility] = mapped_column(
        Enum(CommentVisibility, native_enum=False, length=40), nullable=False
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("LENGTH(body) > 0", name="ck_comments_body_nonempty"),
        Index("ix_comments_complaint_created", "complaint_id", "created_at"),
    )
