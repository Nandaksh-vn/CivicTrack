"""
CivicTrack — Complaints API Router (TRD §8.4, §8.5, §8.6, RBAC-01..05, FR-015, FR-016, FR-024, FR-036..041)
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import (
    ensure_complaint_owner,
    ensure_officer_department,
    get_current_user,
    require_roles,
)
from app.core.clock import utcnow
from app.core.errors import Conflict, NotFound
from app.db.session import get_db
from app.models.complaint import Complaint
from app.models.enums import ImageKind, Role, Status
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification
from app.models.user import User
from app.schemas.department import DepartmentOut
from app.schemas.image import ComplaintImageOut
from app.schemas.superintendent import (
    ComplaintDetailResponse,
    PublicOfficerOut,
    ResolveComplaintRequest,
    ResolveComplaintResponse,
    SuperintendentActionCreate,
    SuperintendentActionResponse,
    TimelineEventOut,
)
from app.services.image_service import resolve_image_file_path, store_complaint_image
from app.services.superintendent_service import (
    get_timeline_events,
    record_superintendent_action,
    resolve_escalated_complaint,
)

router = APIRouter(tags=["Complaints"])


def _get_complaint_or_404(db: Session, complaint_id: int) -> Complaint:
    complaint = db.execute(
        select(Complaint)
        .options(
            joinedload(Complaint.department),
            joinedload(Complaint.resolved_by),
        )
        .where(Complaint.id == complaint_id)
    ).scalar_one_or_none()
    if complaint is None:
        raise NotFound(message="Complaint not found.", error_code="NOT_FOUND")
    return complaint


@router.get(
    "/{complaint_id}",
    status_code=status.HTTP_200_OK,
    response_model=ComplaintDetailResponse,
    summary="Get complaint details with role-scoped access",
)
def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintDetailResponse:
    """
    Retrieve complaint detail (FR-015, FR-018, FR-036).
    Citizen: own complaint only.
    Department Officer: own department only.
    Superintendent & Admin: all complaints.
    """
    complaint = _get_complaint_or_404(db, complaint_id)

    # Scoped access checks
    if current_user.role == Role.CITIZEN:
        ensure_complaint_owner(complaint, current_user)
    elif current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)

    now = utcnow()
    current_overdue = 0
    if complaint.status == Status.ESCALATED and complaint.resolution_due_at:
        current_overdue = max(0, int((now - complaint.resolution_due_at).total_seconds()))

    resolved_by_out = None
    if complaint.resolved_by is not None:
        resolved_by_out = PublicOfficerOut(
            id=complaint.resolved_by.id,
            full_name=complaint.resolved_by.full_name,
        )

    return ComplaintDetailResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        title=complaint.title,
        description=complaint.description,
        location_text=complaint.location_text,
        latitude=float(complaint.latitude) if complaint.latitude is not None else None,
        longitude=float(complaint.longitude) if complaint.longitude is not None else None,
        status=complaint.status,
        department=DepartmentOut.model_validate(complaint.department),
        citizen_id=complaint.citizen_id,
        submitted_at=complaint.submitted_at,
        accepted_at=complaint.accepted_at,
        resolution_due_at=complaint.resolution_due_at,
        escalated_at=complaint.escalated_at,
        overdue_seconds=complaint.sla_seconds,
        current_overdue_seconds=current_overdue,
        resolved_at=complaint.resolved_at,
        resolved_by=resolved_by_out,
        resolution_note=complaint.resolution_note,
        rejected_at=complaint.rejected_at,
        rejection_reason=complaint.rejection_reason,
    )


@router.get(
    "/{complaint_id}/timeline",
    status_code=status.HTTP_200_OK,
    response_model=list[TimelineEventOut],
    summary="Get unified complaint timeline",
)
def get_complaint_timeline(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TimelineEventOut]:
    """Retrieve full chronological timeline for complaint (FR-016, FR-037)."""
    complaint = _get_complaint_or_404(db, complaint_id)

    if current_user.role == Role.CITIZEN:
        ensure_complaint_owner(complaint, current_user)
    elif current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)

    events = get_timeline_events(db, complaint_id)
    return [TimelineEventOut(**e) for e in events]


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
    "/{complaint_id}/superintendent-actions",
    status_code=status.HTTP_201_CREATED,
    response_model=SuperintendentActionResponse,
    summary="Superintendent records action on escalated complaint",
)
def create_superintendent_action(
    complaint_id: int,
    data: SuperintendentActionCreate,
    current_user: User = Depends(require_roles(Role.SUPERINTENDENT_OFFICER)),
    db: Session = Depends(get_db),
) -> SuperintendentActionResponse:
    """
    Superintendent supervisory action (FR-038, FR-039).
    Restricted to ESCALATED complaints. Fans out NT-06 notifications.
    """
    action = record_superintendent_action(
        db=db,
        complaint_id=complaint_id,
        officer=current_user,
        action_type=data.action_type,
        note=data.note,
        directed_department_id=data.directed_department_id,
    )
    return SuperintendentActionResponse(
        id=action.id,
        complaint_id=action.complaint_id,
        action_type=action.action_type,
        note=action.note,
        directed_department=(
            DepartmentOut.model_validate(action.directed_department)
            if action.directed_department
            else None
        ),
        officer=PublicOfficerOut(id=current_user.id, full_name=current_user.full_name),
        created_at=action.created_at,
        notifications_created=["NT-06"],
    )


@router.post(
    "/{complaint_id}/resolve",
    status_code=status.HTTP_200_OK,
    response_model=ResolveComplaintResponse,
    summary="Resolve complaint",
)
def resolve_complaint_endpoint(
    complaint_id: int,
    data: ResolveComplaintRequest | None = None,
    current_user: User = Depends(
        require_roles(Role.DEPARTMENT_OFFICER, Role.SUPERINTENDENT_OFFICER)
    ),
    db: Session = Depends(get_db),
) -> ResolveComplaintResponse:
    """
    Resolve complaint (FR-024, FR-041).
    Superintendent may only resolve from ESCALATED.
    Department Officer resolves assigned/in-progress complaint for their department.
    """
    complaint = _get_complaint_or_404(db, complaint_id)

    if current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)

    if data is None or not (10 <= len(data.note.strip()) <= 2000):
        from app.core.errors import UnprocessableEntity

        raise UnprocessableEntity(
            message="Resolution note must be between 10 and 2000 characters.",
            error_code="VALIDATION_ERROR",
        )

    if current_user.role == Role.SUPERINTENDENT_OFFICER:
        complaint = resolve_escalated_complaint(
            db=db,
            complaint_id=complaint_id,
            officer=current_user,
            note=data.note,
        )
    else:
        # Department Officer path
        if complaint.status == Status.PENDING_DEPARTMENT_REVIEW:
            raise Conflict(
                message="Cannot resolve a complaint directly from pending review.",
                error_code="INVALID_TRANSITION",
            )

        now = utcnow()
        prev_status = complaint.status
        complaint.status = Status.RESOLVED
        complaint.resolved_at = now
        complaint.resolved_by_user_id = current_user.id
        complaint.resolution_note = data.note.strip()

        history = ComplaintStatusHistory(
            complaint_id=complaint.id,
            from_status=prev_status,
            to_status=Status.RESOLVED,
            actor_user_id=current_user.id,
            actor_role=current_user.role.value,
            note=data.note.strip(),
            created_at=now,
        )
        db.add(history)

        notif = Notification(
            recipient_user_id=complaint.citizen_id,
            complaint_id=complaint.id,
            trigger_code="NT-07",
            title=f"Complaint Resolved: {complaint.complaint_number}",
            body=(
                f"Your complaint {complaint.complaint_number} was resolved by "
                f"Officer {current_user.full_name}. Note: {data.note.strip()}"
            ),
            is_read=False,
            created_at=now,
        )
        db.add(notif)
        db.commit()
        db.refresh(complaint)

    return ResolveComplaintResponse(
        id=complaint.id,
        complaint_number=complaint.complaint_number,
        status=complaint.status,
        resolved_at=complaint.resolved_at or utcnow(),
        resolved_by=PublicOfficerOut(
            id=current_user.id,
            full_name=current_user.full_name,
        ),
        resolution_note=complaint.resolution_note or data.note,
        notifications_created=["NT-07"],
    )


# ── Images & Evidence (FR-010, FR-023, TRD §10, NFR-013, SEC-09) ─────────────


@router.post(
    "/{complaint_id}/images",
    status_code=status.HTTP_201_CREATED,
    response_model=ComplaintImageOut,
    summary="Upload image evidence for complaint",
)
async def upload_complaint_image(
    complaint_id: int,
    file: UploadFile = File(...),
    kind: ImageKind = Form(ImageKind.PROGRESS),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ComplaintImageOut:
    """
    Upload image evidence (FR-010, FR-023, TRD §10).
    Validates magic bytes, format, dimensions, size <= 5 MiB.
    """
    complaint = _get_complaint_or_404(db, complaint_id)

    # Scoped authorization
    if current_user.role == Role.CITIZEN:
        ensure_complaint_owner(complaint, current_user)
    elif current_user.role == Role.DEPARTMENT_OFFICER:
        ensure_officer_department(complaint, current_user)

    content = await file.read()
    image = store_complaint_image(
        db=db,
        complaint_id=complaint.id,
        user=current_user,
        content=content,
        filename=file.filename or "evidence.jpg",
        content_type=file.content_type or "image/jpeg",
        kind=kind,
    )
    return ComplaintImageOut.model_validate(image)


@router.get(
    "/{complaint_id}/images/{image_id}/file",
    summary="Download or stream complaint image file",
)
def get_complaint_image_file(
    complaint_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FileResponse:
    """
    Serve image file under authorization check (TRD §10.3).
    Ensures path cannot escape upload root.
    """
    file_path, image = resolve_image_file_path(
        db=db,
        complaint_id=complaint_id,
        image_id=image_id,
        user=current_user,
    )
    return FileResponse(
        path=file_path,
        media_type=image.mime_type,
        filename=image.original_filename,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f'inline; filename="{image.original_filename}"',
        },
    )
