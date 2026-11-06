"""
CivicTrack — Image Schemas (TRD §8, §10)
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import ImageKind


class ComplaintImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    complaint_id: int
    kind: ImageKind
    original_filename: str
    mime_type: str
    size_bytes: int
    created_at: datetime
