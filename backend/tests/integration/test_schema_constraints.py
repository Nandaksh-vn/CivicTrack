"""Phase 4 constraint tests: uniqueness, checks, append-only guard.

Covers:
- complaint_number is unique (BR-01)
- coordinate pairing, range and deadline-requires-acceptance checks (FR-011, BR-05)
- exactly one escalation row per complaint (BR-08, FR-029)
- append-only tables reject UPDATE/DELETE (FR-050, NFR-008)
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from app.core.clock import utcnow
from app.db.guards import AppendOnlyViolation
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.complaint_status_history import ComplaintStatusHistory
from app.models.enums import Priority, Status, TriggerSource
from app.models.escalation import Escalation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def _violation(db: Session):  # noqa: ANN202
    with pytest.raises(IntegrityError):
        db.flush()
    # The shared test DB keeps committed rows; each constraint test ends right
    # after the failing flush, so the poisoned session never leaks downstream.


def test_duplicate_complaint_number_is_rejected(
    db: Session,
    complaint_roads: Complaint,
    cat_streetlight: ComplaintCategory,
    dept_electrical,
    citizen_user,
) -> None:
    citizen, _ = citizen_user
    duplicate = Complaint(
        complaint_number=complaint_roads.complaint_number,
        citizen_id=citizen.id,
        category_id=cat_streetlight.id,
        department_id=dept_electrical.id,
        title="Matching tracking number",
        description="A complaint with the same tracking number must be rejected.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(duplicate)
    _violation(db)


def test_coordinate_pairing_check_constraint(db: Session, citizen_user) -> None:  # noqa: ANN001
    from app.models.department import Department

    department = Department(
        name="Pairing Department",
        code="PAIR",
        description="constraint checks",
        is_active=True,
    )
    db.add(department)
    db.flush()
    category = ComplaintCategory(
        name="Pairing Category",
        code="PAIR-CAT",
        department_id=department.id,
        default_priority=Priority.MEDIUM,
        is_active=True,
    )
    db.add(category)
    db.flush()
    citizen, _ = citizen_user

    bad = Complaint(
        complaint_number="CT-2026-900001",
        citizen_id=citizen.id,
        category_id=category.id,
        department_id=department.id,
        title="Broken coordinate pairing",
        description="Latitude without longitude must be rejected by the check constraint.",
        latitude=12.97,
        longitude=None,
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(bad)
    _violation(db)


def test_coordinate_range_check_constraint(db: Session, citizen_user) -> None:  # noqa: ANN001
    from app.models.department import Department

    department = Department(
        name="Range Department",
        code="RANG",
        description="constraint checks",
        is_active=True,
    )
    db.add(department)
    db.flush()
    category = ComplaintCategory(
        name="Range Category",
        code="RANGE-CAT",
        department_id=department.id,
        default_priority=Priority.MEDIUM,
        is_active=True,
    )
    db.add(category)
    db.flush()
    citizen, _ = citizen_user

    bad = Complaint(
        complaint_number="CT-2026-900002",
        citizen_id=citizen.id,
        category_id=category.id,
        department_id=department.id,
        title="Out of range coordinate",
        description="Latitude 95 is outside the legal range and must be rejected.",
        latitude=95.0,
        longitude=0.0,
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(bad)
    _violation(db)


def test_deadline_without_acceptance_is_rejected(db: Session, citizen_user) -> None:  # noqa: ANN001
    from app.models.department import Department

    department = Department(
        name="Deadline Department",
        code="DEAD",
        description="constraint checks",
        is_active=True,
    )
    db.add(department)
    db.flush()
    category = ComplaintCategory(
        name="Deadline Category",
        code="DEADLINE-CAT",
        department_id=department.id,
        default_priority=Priority.MEDIUM,
        is_active=True,
    )
    db.add(category)
    db.flush()
    citizen, _ = citizen_user

    bad = Complaint(
        complaint_number="CT-2026-900003",
        citizen_id=citizen.id,
        category_id=category.id,
        department_id=department.id,
        title="Deadline before acceptance",
        description="resolution_due_at without accepted_at must be rejected.",
        resolution_due_at=utcnow() + timedelta(days=7),
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(bad)
    _violation(db)


def test_duplicate_escalation_row_is_rejected(
    db: Session,
    escalated_complaint: Complaint,
) -> None:
    first = Escalation(
        complaint_id=escalated_complaint.id,
        previous_status=Status.ACCEPTED,
        deadline_at=utcnow() - timedelta(days=1),
        escalated_at=utcnow() - timedelta(hours=1),
        trigger_source=TriggerSource.SCHEDULER,
    )
    db.add(first)
    db.flush()

    second = Escalation(
        complaint_id=escalated_complaint.id,
        previous_status=Status.ACCEPTED,
        deadline_at=utcnow() - timedelta(days=1),
        escalated_at=utcnow(),
        trigger_source=TriggerSource.MANUAL_TRIGGER,
    )
    db.add(second)
    _violation(db)


def test_append_only_tables_reject_update(
    db: Session,
    complaint_roads: Complaint,
) -> None:
    db.add(
        ComplaintStatusHistory(
            complaint_id=complaint_roads.id,
            from_status=None,
            to_status=Status.SUBMITTED,
            actor_user_id=None,
            actor_role="SYSTEM",
            note="Routed to department.",
        )
    )
    db.flush()

    history = db.scalar(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == complaint_roads.id
        )
    )
    assert history is not None

    history.note = "retouched"
    with pytest.raises(AppendOnlyViolation):
        db.flush()


def test_append_only_tables_reject_delete(
    db: Session,
    complaint_roads: Complaint,
) -> None:
    db.add(
        ComplaintStatusHistory(
            complaint_id=complaint_roads.id,
            from_status=None,
            to_status=Status.SUBMITTED,
            actor_user_id=None,
            actor_role="SYSTEM",
            note="Routed to department.",
        )
    )
    db.flush()

    history = db.scalar(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == complaint_roads.id
        )
    )
    assert history is not None
    db.delete(history)
    with pytest.raises(AppendOnlyViolation):
        db.flush()
