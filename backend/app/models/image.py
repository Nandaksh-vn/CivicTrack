"""
CivicTrack — Complaint Image Model (TRD §7.6)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

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
        Enum(ImageKind, native_enum=False, length=30),
        default=ImageKind.SUBMISSION,
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    complaint = relationship("Complaint", back_populates="images")
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_user_id])

    __table_args__ = (Index("ix_complaint_images_comp_kind", "complaint_id", "kind", "created_at"),)
