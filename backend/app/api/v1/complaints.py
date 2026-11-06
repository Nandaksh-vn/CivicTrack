"""
CivicTrack — Complaints API Router (TRD §8.4, §8.5, RBAC-01..05)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import (
    ensure_complaint_owner,
    ensure_officer_department,
    ensure_superintendent_action_allowed,
    get_current_user,
    require_roles,
)
from app.core.errors import NotFound
from app.db.session import get_db
from app.models.complaint import Complaint
from app.models.enums import Role
from app.models.user import User

router = APIRouter(tags=["Complaints"])


def _get_complaint_or_404(db: Session, complaint_id: int) -> Complaint:
    complaint = db.execute(
        select(Complaint).where(Complaint.id == complaint_id)
    ).scalar_one_or_none()
    if complaint is None:
        raise NotFound(message="Complaint not found.", error_code="NOT_FOUND")
    return complaint


@router.get(
    "/{complaint_id}",
    status_code=status.HTTP_200_OK,
    summary="Get complaint details",
)
def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Retrieve complaint detail with role/object-scope check (FR-015, FR-018)."""
    complaint = _get_complaint_or_404(db, complaint_id)

    # Scoped access checks
    if current_user.role == Role.CITIZEN:
        ensure_complaint_owner(complaint, current_user)
    elif current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)

    return {
        "id": complaint.id,
        "complaint_number": complaint.complaint_number,
        "title": complaint.title,
        "status": complaint.status.value,
        "department_id": complaint.department_id,
        "citizen_id": complaint.citizen_id,
    }


@router.post(
    "/{complaint_id}/accept",
    status_code=status.HTTP_200_OK,
    summary="Department Officer accepts complaint",
)
def accept_complaint(
    complaint_id: int,
    current_user: User = Depends(require_roles(Role.DEPARTMENT_OFFICER)),
    db: Session = Depends(get_db),
) -> dict:
    """Department officer accepts complaint (FR-019)."""
    complaint = _get_complaint_or_404(db, complaint_id)
    ensure_officer_department(complaint, current_user)
    return {"id": complaint.id, "status": "ACCEPTED"}


@router.post(
    "/{complaint_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Department Officer rejects complaint",
)
def reject_complaint(
    complaint_id: int,
    current_user: User = Depends(require_roles(Role.DEPARTMENT_OFFICER)),
    db: Session = Depends(get_db),
) -> dict:
    """Department officer rejects complaint (FR-020)."""
    complaint = _get_complaint_or_404(db, complaint_id)
    ensure_officer_department(complaint, current_user)
    return {"id": complaint.id, "status": "REJECTED"}


@router.post(
    "/{complaint_id}/resolve",
    status_code=status.HTTP_200_OK,
    summary="Resolve complaint",
)
def resolve_complaint(
    complaint_id: int,
    current_user: User = Depends(
        require_roles(Role.DEPARTMENT_OFFICER, Role.SUPERINTENDENT_OFFICER)
    ),
    db: Session = Depends(get_db),
) -> dict:
    """Resolve complaint (FR-024, FR-041)."""
    complaint = _get_complaint_or_404(db, complaint_id)
    if current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)
    elif current_user.role == Role.SUPERINTENDENT_OFFICER:
        ensure_superintendent_action_allowed(complaint, current_user)
    return {"id": complaint.id, "status": "RESOLVED"}


@router.post(
    "/{complaint_id}/superintendent-actions",
    status_code=status.HTTP_201_CREATED,
    summary="Superintendent records action on escalated complaint",
)
def create_superintendent_action(
    complaint_id: int,
    current_user: User = Depends(require_roles(Role.SUPERINTENDENT_OFFICER)),
    db: Session = Depends(get_db),
) -> dict:
    """Superintendent supervisory action (FR-038)."""
    complaint = _get_complaint_or_404(db, complaint_id)
    ensure_superintendent_action_allowed(complaint, current_user)
    return {"id": 1, "complaint_id": complaint.id, "status": "ACTION_RECORDED"}
