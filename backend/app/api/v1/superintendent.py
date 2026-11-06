"""
CivicTrack — Superintendent Oversight API Router (FR-035..041, TRD §8.6)
"""

from __future__ import annotations

import math

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.enums import Role
from app.models.user import User
from app.schemas.superintendent import (
    EscalatedComplaintItem,
    EscalationQueueResponse,
    EscalationQueueSummary,
)
from app.services.superintendent_service import get_escalation_queue

router = APIRouter(tags=["Superintendent"])


@router.get(
    "/escalations",
    status_code=status.HTTP_200_OK,
    response_model=EscalationQueueResponse,
    summary="Get escalation queue ordered by overdue duration descending",
)
def get_escalations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: User = Depends(require_roles(Role.SUPERINTENDENT_OFFICER)),
    db: Session = Depends(get_db),
) -> EscalationQueueResponse:
    """
    Superintendent queue of ESCALATED complaints (FR-035, FR-040).
    Sorted by overdue duration descending; computes current_overdue_seconds at request time.
    """
    items, summary, total = get_escalation_queue(db=db, page=page, page_size=page_size)
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return EscalationQueueResponse(
        items=[EscalatedComplaintItem.model_validate(item) for item in items],
        summary=EscalationQueueSummary(**summary),
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.get(
    "/summary",
    status_code=status.HTTP_200_OK,
    response_model=EscalationQueueSummary,
    summary="Get escalation metrics summary",
)
def get_escalation_summary(
    _: User = Depends(require_roles(Role.SUPERINTENDENT_OFFICER)),
    db: Session = Depends(get_db),
) -> EscalationQueueSummary:
    """Escalation metrics summary (FR-035)."""
    _, summary, _ = get_escalation_queue(db=db, page=1, page_size=1)
    return EscalationQueueSummary(**summary)
