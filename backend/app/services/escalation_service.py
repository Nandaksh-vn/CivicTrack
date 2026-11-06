"""
CivicTrack — Escalation Engine Service (TRD §11, FR-028..FR-034, NFR-002, NFR-003, AC-08)
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.models.complaint import Complaint
from app.models.enums import Role, Status, TriggerSource
from app.models.escalation import Escalation
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification
from app.models.user import User

logger = logging.getLogger(__name__)


def process_escalations(
    db: Session,
    as_of: datetime | None = None,
    trigger_source: TriggerSource = TriggerSource.SCHEDULER,
) -> int:
    """
    Find overdue complaints and escalate them atomically and idempotently (FR-028..FR-031, AC-08).
    Returns count of complaints escalated in this run.
    """
    now = as_of or utcnow()

    # Query candidate complaints that are accepted or in progress and past their deadline
    stmt = (
        select(Complaint)
        .where(
            Complaint.status.in_([Status.ACCEPTED, Status.IN_PROGRESS]),
            Complaint.resolution_due_at.is_not(None),
            Complaint.resolution_due_at <= now,
        )
        .order_by(Complaint.resolution_due_at.asc())
    )
    candidates = list(db.scalars(stmt).all())

    escalated_count = 0

    for complaint in candidates:
        # Re-check status inside transaction to prevent race conditions (FR-029)
        if complaint.status not in (Status.ACCEPTED, Status.IN_PROGRESS):
            continue

        # Check unique constraint / existing escalation record (idempotency guard)
        existing_esc = db.scalar(select(Escalation).where(Escalation.complaint_id == complaint.id))
        if existing_esc:
            continue

        prev_status = complaint.status
        overdue_secs = max(0, int((now - complaint.resolution_due_at).total_seconds()))

        try:
            # 1. Update complaint status
            complaint.status = Status.ESCALATED
            complaint.escalated_at = now

            # 2. Add status history
            history = ComplaintStatusHistory(
                complaint_id=complaint.id,
                from_status=prev_status,
                to_status=Status.ESCALATED,
                actor_user_id=None,
                actor_role="SYSTEM",
                note="Automatic escalation: SLA deadline exceeded without resolution.",
                created_at=now,
            )
            db.add(history)

            # 3. Add escalation record
            esc_record = Escalation(
                complaint_id=complaint.id,
                escalation_number=1,
                previous_status=prev_status,
                deadline_at=complaint.resolution_due_at,
                escalated_at=now,
                overdue_seconds=overdue_secs,
                trigger_source=trigger_source,
                reason_code="SLA_BREACH",
                created_at=now,
            )
            db.add(esc_record)

            # 4. Fan out notifications (NT-05): Citizen, Superintendent, Department Officers
            recipients: set[int] = {complaint.citizen_id}

            # Find department officers
            dept_officers = db.scalars(
                select(User.id).where(
                    User.department_id == complaint.department_id,
                    User.role == Role.DEPARTMENT_OFFICER,
                    User.is_active.is_(True),
                )
            ).all()
            recipients.update(dept_officers)

            # Find superintendents
            supers = db.scalars(
                select(User.id).where(
                    User.role == Role.SUPERINTENDENT_OFFICER,
                    User.is_active.is_(True),
                )
            ).all()
            recipients.update(supers)

            for uid in recipients:
                db.add(
                    Notification(
                        recipient_user_id=uid,
                        complaint_id=complaint.id,
                        trigger_code="NT-05",
                        title=f"Complaint Escalated: {complaint.complaint_number}",
                        body=(
                            f"Complaint {complaint.complaint_number} ({complaint.title}) "
                            f"exceeded its SLA deadline and has been escalated to the Superintendent."
                        ),
                        is_read=False,
                        created_at=now,
                    )
                )

            db.commit()
            escalated_count += 1
            logger.info(
                "event=complaint_escalated complaint_id=%s complaint_number=%s overdue_seconds=%s",
                complaint.id,
                complaint.complaint_number,
                overdue_secs,
            )
        except Exception as exc:
            db.rollback()
            logger.warning(
                "Failed to escalate complaint %s (possible concurrent run): %s",
                complaint.id,
                exc,
            )

    return escalated_count
