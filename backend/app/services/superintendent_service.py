"""
CivicTrack — Superintendent Oversight Service (FR-035..041, TRD §5.5, §8.6)
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.clock import utcnow
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.models.audit import AuditLog
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import OfficerActionType, Role, Status
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification
from app.models.officer_action import OfficerAction
from app.models.user import User

logger = logging.getLogger(__name__)


def get_escalation_queue(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict[str, Any]], dict[str, int], int]:
    """
    Retrieve queue of ESCALATED complaints sorted by overdue duration descending (FR-035, FR-040).
    Computes current_overdue_seconds at request time.
    """
    page = max(1, page)
    page_size = min(max(1, page_size), 100)
    now = utcnow()

    # Total open escalated complaints
    total = db.execute(
        select(func.count(Complaint.id)).where(Complaint.status == Status.ESCALATED)
    ).scalar_one()

    # Fetch all open escalated complaints to order by computed overdue duration
    query = (
        select(Complaint)
        .options(joinedload(Complaint.department))
        .where(Complaint.status == Status.ESCALATED)
    )
    complaints = list(db.execute(query).scalars().all())

    # Process items with computed overdue
    items_data: list[dict[str, Any]] = []
    oldest_overdue = 0

    for c in complaints:
        if c.resolution_due_at:
            overdue = max(0, int((now - c.resolution_due_at).total_seconds()))
        elif c.escalated_at:
            overdue = max(0, int((now - c.escalated_at).total_seconds()))
        else:
            overdue = 0

        if overdue > oldest_overdue:
            oldest_overdue = overdue

        # Fetch latest action timestamp
        last_action = db.execute(
            select(OfficerAction.created_at)
            .where(OfficerAction.complaint_id == c.id)
            .order_by(OfficerAction.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()

        items_data.append(
            {
                "id": c.id,
                "complaint_number": c.complaint_number,
                "title": c.title,
                "department": c.department,
                "accepted_at": c.accepted_at,
                "resolution_due_at": c.resolution_due_at,
                "escalated_at": c.escalated_at,
                "overdue_seconds": c.sla_seconds or 0,
                "current_overdue_seconds": overdue,
                "status": c.status,
                "last_action_at": last_action,
            }
        )

    # Sort descending by current_overdue_seconds
    items_data.sort(key=lambda x: x["current_overdue_seconds"], reverse=True)

    # Paginate in memory
    offset = (page - 1) * page_size
    paginated_items = items_data[offset : offset + page_size]

    summary = {
        "open": total,
        "oldest_overdue_seconds": oldest_overdue,
    }

    return paginated_items, summary, total


def record_superintendent_action(
    db: Session,
    complaint_id: int,
    officer: User,
    action_type: OfficerActionType,
    note: str,
    directed_department_id: int | None = None,
) -> OfficerAction:
    """
    Record an append-only supervisory action on an ESCALATED complaint (FR-038, FR-039).
    Creates NT-06 notifications for responsible department officers and the citizen.
    Does not modify the original department_id in P0.
    """
    complaint = db.execute(
        select(Complaint)
        .options(joinedload(Complaint.department))
        .where(Complaint.id == complaint_id)
    ).scalar_one_or_none()

    if complaint is None:
        raise NotFound(message="Complaint not found.", error_code="NOT_FOUND")

    if complaint.status != Status.ESCALATED:
        raise Conflict(
            message="Superintendent can only record actions on escalated complaints.",
            error_code="INVALID_TRANSITION",
        )

    if directed_department_id is not None:
        directed_dept = db.execute(
            select(Department).where(
                Department.id == directed_department_id, Department.is_active.is_(True)
            )
        ).scalar_one_or_none()
        if directed_dept is None:
            raise UnprocessableEntity(
                message="Directed department does not exist or is inactive.",
                error_code="INVALID_DEPARTMENT",
            )

    action = OfficerAction(
        complaint_id=complaint.id,
        officer_user_id=officer.id,
        action_type=action_type,
        directed_department_id=directed_department_id,
        note=note.strip(),
        created_at=utcnow(),
    )
    db.add(action)
    db.flush()

    # Recipient resolution for NT-06 (FR-038, FR-045, NT-06)
    # 1. Citizen owner
    recipients = {complaint.citizen_id}

    # 2. Department officers of responsible department
    dept_officers = (
        db.execute(
            select(User.id).where(
                User.department_id == complaint.department_id,
                User.role == Role.DEPARTMENT_OFFICER,
                User.is_active.is_(True),
            )
        )
        .scalars()
        .all()
    )
    recipients.update(dept_officers)

    # 3. Directed department officers if different
    if directed_department_id and directed_department_id != complaint.department_id:
        dir_officers = (
            db.execute(
                select(User.id).where(
                    User.department_id == directed_department_id,
                    User.role == Role.DEPARTMENT_OFFICER,
                    User.is_active.is_(True),
                )
            )
            .scalars()
            .all()
        )
        recipients.update(dir_officers)

    now = utcnow()
    for uid in recipients:
        notif = Notification(
            recipient_user_id=uid,
            complaint_id=complaint.id,
            trigger_code="NT-06",
            title=f"Supervisory Action Recorded: {complaint.complaint_number}",
            body=(
                f"Superintendent {officer.full_name} recorded action {action_type.value}: "
                f"{note[:200]} at {now.isoformat()}Z."
            ),
            is_read=False,
            created_at=now,
        )
        db.add(notif)

    # Audit log
    audit = AuditLog(
        actor_user_id=officer.id,
        actor_role=officer.role.value,
        action="SUPERINTENDENT_ACTION",
        entity_type="COMPLAINT",
        entity_id=str(complaint.id),
    )
    db.add(audit)
    db.commit()

    # Reload action with relationships
    action_loaded = db.execute(
        select(OfficerAction)
        .options(
            joinedload(OfficerAction.officer),
            joinedload(OfficerAction.directed_department),
        )
        .where(OfficerAction.id == action.id)
    ).scalar_one()

    logger.info(
        "event=superintendent_action complaint_id=%s action_type=%s officer_id=%s",
        complaint.id,
        action_type.value,
        officer.id,
    )
    return action_loaded


def resolve_escalated_complaint(
    db: Session,
    complaint_id: int,
    officer: User,
    note: str,
) -> Complaint:
    """
    Resolve an ESCALATED complaint by Superintendent (FR-041).
    Records resolution note, status history, and NT-07 notification.
    Complaint leaves the escalation queue.
    """
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

    if complaint.status != Status.ESCALATED:
        raise Conflict(
            message="Superintendent can only resolve escalated complaints.",
            error_code="INVALID_TRANSITION",
        )

    now = utcnow()
    prev_status = complaint.status

    complaint.status = Status.RESOLVED
    complaint.resolved_at = now
    complaint.resolved_by_user_id = officer.id
    complaint.resolution_note = note.strip()

    # Append to status history (FR-050, BR-10)
    history = ComplaintStatusHistory(
        complaint_id=complaint.id,
        from_status=prev_status,
        to_status=Status.RESOLVED,
        actor_user_id=officer.id,
        actor_role=officer.role.value,
        note=f"Resolved by Superintendent: {note.strip()}",
        created_at=now,
    )
    db.add(history)

    # NT-07 for citizen owner (FR-024, FR-041, NT-07)
    notif = Notification(
        recipient_user_id=complaint.citizen_id,
        complaint_id=complaint.id,
        trigger_code="NT-07",
        title=f"Complaint Resolved: {complaint.complaint_number}",
        body=(
            f"Your complaint {complaint.complaint_number} was resolved by "
            f"Superintendent {officer.full_name} on {now.isoformat()}Z. "
            f"Note: {note.strip()}"
        ),
        is_read=False,
        created_at=now,
    )
    db.add(notif)

    # Audit log
    audit = AuditLog(
        actor_user_id=officer.id,
        actor_role=officer.role.value,
        action="COMPLAINT_RESOLVED",
        entity_type="COMPLAINT",
        entity_id=str(complaint.id),
    )
    db.add(audit)
    db.commit()

    # Reload complaint
    reloaded = db.execute(
        select(Complaint)
        .options(
            joinedload(Complaint.department),
            joinedload(Complaint.resolved_by),
        )
        .where(Complaint.id == complaint.id)
    ).scalar_one()

    logger.info(
        "event=complaint_resolved_by_superintendent complaint_id=%s officer_id=%s",
        complaint.id,
        officer.id,
    )
    return reloaded


def get_timeline_events(db: Session, complaint_id: int) -> list[dict[str, Any]]:
    """
    Retrieve unified timeline events sorted chronologically ascending (FR-016, FR-037, FR-050).
    """
    events: list[dict[str, Any]] = []

    # 1. Status history events
    history_rows = (
        db.execute(
            select(ComplaintStatusHistory)
            .options(joinedload(ComplaintStatusHistory.actor))
            .where(ComplaintStatusHistory.complaint_id == complaint_id)
            .order_by(ComplaintStatusHistory.created_at.asc())
        )
        .scalars()
        .all()
    )

    for h in history_rows:
        events.append(
            {
                "event_type": "STATUS_CHANGE",
                "created_at": h.created_at,
                "actor_name": h.actor.full_name if h.actor else "System",
                "actor_role": h.actor_role,
                "note": h.note,
                "from_status": h.from_status.value if h.from_status else None,
                "to_status": h.to_status.value,
                "details": {},
            }
        )

    # 2. Officer actions
    actions = (
        db.execute(
            select(OfficerAction)
            .options(
                joinedload(OfficerAction.officer),
                joinedload(OfficerAction.directed_department),
            )
            .where(OfficerAction.complaint_id == complaint_id)
            .order_by(OfficerAction.created_at.asc())
        )
        .scalars()
        .all()
    )

    for a in actions:
        events.append(
            {
                "event_type": f"SUPERINTENDENT_{a.action_type.value}",
                "created_at": a.created_at,
                "actor_name": a.officer.full_name,
                "actor_role": a.officer.role.value,
                "note": a.note,
                "from_status": None,
                "to_status": None,
                "details": {
                    "directed_department": (
                        a.directed_department.name if a.directed_department else None
                    ),
                },
            }
        )

    events.sort(key=lambda x: x["created_at"])
    return events
