"""
CivicTrack — Department Model (TRD §7.3)
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.clock import utcnow
from app.db.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    users = relationship("User", back_populates="department")
