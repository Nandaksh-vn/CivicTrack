"""
CivicTrack — Dependency / RBAC Unit Tests (RBAC-01..08, AC-14)

Tests object scope guards and role-checking logic without requiring HTTP.
"""

from __future__ import annotations

import pytest
from app.core.errors import Conflict, Forbidden
from app.models.complaint import Complaint
from app.models.enums import Role, Status
from app.models.user import User

# ── ensure_complaint_owner ───────────────────────────────────────────────────


def test_ensure_complaint_owner_allows_owner() -> None:
    complaint = Complaint(id=1, citizen_id=42, title="t", description="d")
    user = User(id=42, email="a@b.com", password_hash="x", role=Role.CITIZEN)
    from app.dependencies import ensure_complaint_owner

    ensure_complaint_owner(complaint, user)


def test_ensure_complaint_owner_rejects_non_owner() -> None:
    complaint = Complaint(id=1, citizen_id=42, title="t", description="d")
    user = User(id=99, email="b@c.com", password_hash="x", role=Role.CITIZEN)
    from app.dependencies import ensure_complaint_owner

    with pytest.raises(Forbidden) as exc:
        ensure_complaint_owner(complaint, user)
    assert exc.value.error_code == "FORBIDDEN"


def test_ensure_complaint_owner_allows_staff() -> None:
    complaint = Complaint(id=1, citizen_id=42, title="t", description="d")
    for role in (Role.DEPARTMENT_OFFICER, Role.SUPERINTENDENT_OFFICER, Role.PLATFORM_ADMIN):
        user = User(id=99, email="s@c.com", password_hash="x", role=role)
        from app.dependencies import ensure_complaint_owner

        ensure_complaint_owner(complaint, user)  # no raise for non-citizen


# ── ensure_officer_department ────────────────────────────────────────────────


def test_ensure_officer_department_allows_same_dept() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", department_id=7)
    user = User(
        id=9,
        email="o@d.com",
        password_hash="x",
        role=Role.DEPARTMENT_OFFICER,
        department_id=7,
    )
    from app.dependencies import ensure_officer_department

    ensure_officer_department(complaint, user)  # no raise


def test_ensure_officer_department_rejects_other_dept() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", department_id=7)
    user = User(
        id=9,
        email="o@d.com",
        password_hash="x",
        role=Role.DEPARTMENT_OFFICER,
        department_id=8,
    )
    from app.dependencies import ensure_officer_department

    with pytest.raises(Forbidden):
        ensure_officer_department(complaint, user)


def test_ensure_officer_department_rejects_no_department() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", department_id=7)
    user = User(
        id=9,
        email="o@d.com",
        password_hash="x",
        role=Role.DEPARTMENT_OFFICER,
        department_id=None,
    )
    from app.dependencies import ensure_officer_department

    with pytest.raises(Forbidden):
        ensure_officer_department(complaint, user)


def test_ensure_officer_department_allows_non_officer() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", department_id=7)
    for role in (Role.CITIZEN, Role.SUPERINTENDENT_OFFICER, Role.PLATFORM_ADMIN):
        user = User(id=9, email="u@d.com", password_hash="x", role=role)
        from app.dependencies import ensure_officer_department

        ensure_officer_department(complaint, user)  # no raise for non-officer


# ── ensure_superintendent_action_allowed ─────────────────────────────────────


def test_ensure_superintendent_allows_escalated() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", status=Status.ESCALATED)
    user = User(id=9, email="s@d.com", password_hash="x", role=Role.SUPERINTENDENT_OFFICER)
    from app.dependencies import ensure_superintendent_action_allowed

    ensure_superintendent_action_allowed(complaint, user)  # no raise


def test_ensure_superintendent_rejects_non_escalated() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", status=Status.ACCEPTED)
    user = User(id=9, email="s@d.com", password_hash="x", role=Role.SUPERINTENDENT_OFFICER)
    from app.dependencies import ensure_superintendent_action_allowed

    with pytest.raises(Conflict) as exc:
        ensure_superintendent_action_allowed(complaint, user)
    assert exc.value.error_code == "INVALID_TRANSITION"


def test_ensure_superintendent_allows_non_superintendent() -> None:
    complaint = Complaint(id=1, citizen_id=1, title="t", description="d", status=Status.ACCEPTED)
    for role in (Role.CITIZEN, Role.DEPARTMENT_OFFICER, Role.PLATFORM_ADMIN):
        user = User(id=9, email="u@d.com", password_hash="x", role=role)
        from app.dependencies import ensure_superintendent_action_allowed

        ensure_superintendent_action_allowed(complaint, user)  # no raise
