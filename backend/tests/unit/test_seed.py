"""
CivicTrack — Unit test for Seed Script (DEP-009, US-ADM-06)
Verifies seed creates standard departments, categories, users, complaints in every status,
and that re-running seed is strictly idempotent.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Status
from app.models.user import User
from app.seed import seed_database


def test_seed_database_execution_and_idempotency(db):
    """Seed must create demo entities and run twice without error or duplicate keys."""
    # First seed run
    seed_database(db)

    # Verify departments
    depts = db.execute(select(Department)).scalars().all()
    assert len(depts) >= 4
    dept_codes = {d.code for d in depts}
    assert {"WTR", "RDS", "ELE", "SAN"}.issubset(dept_codes)

    # Verify categories
    cats = db.execute(select(ComplaintCategory)).scalars().all()
    assert len(cats) >= 4

    # Verify users
    users = db.execute(select(User)).scalars().all()
    assert len(users) >= 6
    user_emails = {u.email for u in users}
    assert "admin@civictrack.local" in user_emails
    assert "superintendent@civictrack.local" in user_emails
    assert "officer.water@civictrack.local" in user_emails
    assert "citizen.jane@civictrack.local" in user_emails

    # Verify complaints in all P0 statuses
    complaints = db.execute(select(Complaint)).scalars().all()
    assert len(complaints) >= 6
    statuses = {c.status for c in complaints}
    assert {
        Status.SUBMITTED,
        Status.IN_PROGRESS,
        Status.ESCALATED,
        Status.RESOLVED,
        Status.REJECTED,
    }.issubset(statuses)

    from app.core.clock import utcnow

    # Verify guaranteed overdue candidate
    overdue_candidate = db.execute(
        select(Complaint).where(Complaint.complaint_number == "CT-DEMO-003")
    ).scalar_one_or_none()
    assert overdue_candidate is not None
    assert overdue_candidate.status == Status.IN_PROGRESS
    assert overdue_candidate.resolution_due_at is not None
    assert overdue_candidate.resolution_due_at < utcnow()

    # Second seed run must be strictly idempotent
    seed_database(db)
    depts_second = db.execute(select(Department)).scalars().all()
    assert len(depts_second) == len(depts)
