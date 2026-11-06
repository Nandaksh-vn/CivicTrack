"""
CivicTrack — Escalation Concurrency & Idempotency Tests (TEST-055, AC-08, NFR-003, NFR-011)
"""

from __future__ import annotations

from datetime import timedelta

from app.core.clock import utcnow
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Status
from app.models.escalation import Escalation
from app.models.history import ComplaintStatusHistory
from app.models.user import User
from app.services.escalation_service import process_escalations
from sqlalchemy import func, select
from sqlalchemy.orm import Session


def test_escalation_repeated_20_times_is_strictly_idempotent(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """
    AC-08, NFR-003, TEST-055:
    Repeating the escalation check 20 times produces exactly one escalation row
    and exactly one escalation transition.
    """
    citizen, _ = citizen_user
    now = utcnow()

    # Create an overdue complaint
    comp = Complaint(
        complaint_number="CT-2026-000551",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Overdue for 20x Test",
        description="Pothole description.",
        status=Status.ACCEPTED,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(days=8),
        sla_seconds=604800,
        resolution_due_at=now - timedelta(hours=24),  # overdue by 24 hours
    )
    db.add(comp)
    db.commit()
    db.refresh(comp)

    # First run escalates the complaint
    count_first = process_escalations(db, as_of=now)
    assert count_first == 1

    # Runs 2 through 20 should do nothing (idempotent)
    for _ in range(19):
        count_subsequent = process_escalations(db, as_of=now)
        assert count_subsequent == 0

    # Verify single escalation record
    esc_rows = db.scalars(select(Escalation).where(Escalation.complaint_id == comp.id)).all()
    assert len(esc_rows) == 1
    assert esc_rows[0].overdue_seconds >= 86400

    # Verify single history transition to ESCALATED
    history_rows = db.scalars(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == comp.id,
            ComplaintStatusHistory.to_status == Status.ESCALATED,
        )
    ).all()
    assert len(history_rows) == 1

    # Verify final complaint status is ESCALATED
    db.refresh(comp)
    assert comp.status == Status.ESCALATED


def test_escalation_parallel_run_idempotency(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """
    TEST-055, NFR-003:
    Simultaneous execution of escalation passes produces exactly 1 escalation row.
    """
    citizen, _ = citizen_user
    now = utcnow()

    comp = Complaint(
        complaint_number="CT-2026-000552",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Parallel Overdue Complaint",
        description="Parallel description.",
        status=Status.ACCEPTED,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(days=10),
        sla_seconds=604800,
        resolution_due_at=now - timedelta(days=2),
    )
    db.add(comp)
    db.commit()

    # Consecutive rapid-fire passes simulating simultaneous trigger calls
    res1 = process_escalations(db, as_of=now)
    res2 = process_escalations(db, as_of=now)
    res3 = process_escalations(db, as_of=now)

    # Exactly 1 complaint escalated across all runs
    assert res1 == 1
    assert res2 == 0
    assert res3 == 0

    total_esc = (
        db.scalar(select(func.count(Escalation.id)).where(Escalation.complaint_id == comp.id)) or 0
    )
    assert total_esc == 1


def test_worker_restart_and_catch_up(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """
    TEST-055, NFR-011:
    Worker restart / catch-up: overdue complaints created while worker was offline
    are correctly detected and escalated on next pass without data loss.
    """
    citizen, _ = citizen_user
    now = utcnow()

    # Backdated complaint created while worker was 'down'
    offline_comp = Complaint(
        complaint_number="CT-2026-000553",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Complaint Created During Worker Outage",
        description="Description.",
        status=Status.IN_PROGRESS,
        priority=Priority.MEDIUM,
        accepted_at=now - timedelta(days=15),
        sla_seconds=604800,
        resolution_due_at=now - timedelta(days=7),
    )
    db.add(offline_comp)
    db.commit()

    # Worker boots and runs catch-up pass
    escalated = process_escalations(db, as_of=now)
    assert escalated >= 1

    db.refresh(offline_comp)
    assert offline_comp.status == Status.ESCALATED
