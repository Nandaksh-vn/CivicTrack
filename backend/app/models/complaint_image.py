"""`complaint_images` - evidence attached to a complaint or action."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.clock import utcnow
from app.db.base import Base
from app.models.enums import ImageKind


class ComplaintImage(Base):
    __tablename__ = "complaint_images"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        ForeignKey("complaints.id", ondelete="RESTRICT"), nullable=False
    )
    uploaded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    kind: Mapped[ImageKind] = mapped_column(
        Enum(ImageKind, native_enum=False, length=20), nullable=False
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("size_bytes >= 0", name="ck_complaint_images_size_nonnegative"),
        Index("ix_complaint_images_complaint_created", "complaint_id", "created_at"),
    )
