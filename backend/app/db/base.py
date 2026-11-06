"""
CivicTrack — SQLAlchemy declarative base
All ORM models must import Base from this module so Alembic can discover them.
"""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass

