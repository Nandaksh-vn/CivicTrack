"""
CivicTrack — Department Schemas (TRD §8)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
