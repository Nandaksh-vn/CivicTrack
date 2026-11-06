"""
CivicTrack — Department Operations API Router (FR-017, TRD §8.5)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import require_roles
from app.models.enums import Role
from app.models.user import User

router = APIRouter(tags=["Department"])


@router.get(
    "/complaints",
    status_code=status.HTTP_200_OK,
    summary="Get department complaint queue",
)
def get_department_complaints(
    current_user: User = Depends(require_roles(Role.DEPARTMENT_OFFICER)),
) -> dict:
    """Department complaint queue (accessible by Department Officer only)."""
    return {
        "items": [],
        "department_id": current_user.department_id,
        "page": 1,
        "page_size": 20,
        "total": 0,
    }
