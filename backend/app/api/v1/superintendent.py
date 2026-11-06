"""
CivicTrack — Superintendent Oversight API Router (FR-035, TRD §8.6)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app.api.deps import require_roles
from app.models.enums import Role
from app.models.user import User

router = APIRouter(tags=["Superintendent"])


@router.get(
    "/escalations",
    status_code=status.HTTP_200_OK,
    summary="Get escalation queue",
)
def get_escalations(
    _: User = Depends(require_roles(Role.SUPERINTENDENT_OFFICER)),
) -> dict:
    """Escalation queue (accessible by Superintendent Officer only)."""
    return {
        "items": [],
        "page": 1,
        "page_size": 20,
        "total": 0,
    }
