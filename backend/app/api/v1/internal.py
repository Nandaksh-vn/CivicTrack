"""
CivicTrack - Internal operations API (BE-075, BE-076, FR-034).

Token-protected endpoints used by the escalation worker, operators, and the
demo script. These routes are mounted under /internal only and are never
exposed through the public API router.
"""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.errors import Unauthorized
from app.db.session import get_db
from app.models.complaint import Complaint
from app.models.enums import Status
from app.models.escalation import Escalation
from app.services.escalation_service import process_escalations

router = APIRouter(tags=["Internal"])


def verify_internal_token(x_internal_token: str | None = Header(default=None)) -> None:
    """Require the shared internal token for every /internal/* request (BE-017)."""
    if not x_internal_token or not secrets.compare_digest(
        x_internal_token, settings.internal_trigger_token
    ):
        raise Unauthorized(
            message="A valid internal token is required.",
            error_code="INVALID_INTERNAL_TOKEN",
        )


def _count_candidates(db: Session) -> int:
    return (
        db.scalar(
            select(func.count(Complaint.id)).where(
                Complaint.status.in_([Status.ACCEPTED, Status.IN_PROGRESS]),
                Complaint.resolution_due_at.is_not(None),
                Complaint.resolution_due_at <= utcnow(),
            )
        )
        or 0
    )


@router.post(
    "/escalations/run",
    status_code=status.HTTP_200_OK,
    summary="Run the escalation scan once",
    dependencies=[Depends(verify_internal_token)],
)
@router.post(
    "/escalations/trigger",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
    dependencies=[Depends(verify_internal_token)],
)
def run_escalations(db: Session = Depends(get_db)) -> dict[str, int]:
    """Evaluate overdue complaints and return run counters (FR-034)."""
    evaluated = _count_candidates(db)
    escalated = process_escalations(db)
    return {
        "evaluated": evaluated,
        "escalated": escalated,
        "skipped": max(evaluated - escalated, 0),
    }


@router.get(
    "/escalation-status",
    status_code=status.HTTP_200_OK,
    summary="Escalation engine configuration and last-run metadata",
    dependencies=[Depends(verify_internal_token)],
)
def escalation_status(db: Session = Depends(get_db)) -> dict[str, object]:
    """Return the effective SLA window and the latest escalation timestamp (BE-076)."""
    last_escalation_at = db.scalar(select(func.max(Escalation.escalated_at)))
    return {
        "effective_window_minutes": settings.escalation_window_minutes,
        "production_window_minutes": 10_080,
        "demo_mode": settings.demo_mode,
        "check_interval_seconds": settings.escalation_check_seconds,
        "last_escalation_at": last_escalation_at,
        "checked_at": utcnow(),
    }
