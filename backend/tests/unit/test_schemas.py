"""
CivicTrack — Schema Unit Tests (FR-001, FR-002, FR-006)

Tests Pydantic schema validation for authentication, user administration,
and department responses without requiring a database connection.
"""

from __future__ import annotations

import pytest
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.department import DepartmentOut
from app.schemas.user import AdminUserCreate, AdminUserUpdate, PublicUser
from pydantic import ValidationError

_BASE_REGISTER = {
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "ValidPass1",
}


# ── RegisterRequest ──────────────────────────────────────────────────────────


def test_register_request_valid() -> None:
    data = RegisterRequest(
        full_name="Priya Sharma",
        email="Priya@Example.COM",
        password="ValidPass1",
        phone="+91 98765 43210",
    )
    assert data.email == "priya@example.com"
    assert data.phone == "+91 98765 43210"


@pytest.mark.parametrize(
    "field,value",
    [
        ("full_name", "A"),  # < 2 chars
        ("full_name", "x" * 121),  # > 120 chars
        ("email", "not-an-email"),
        ("email", "x" * 200),  # > 190 chars
        ("password", "short"),  # < 8 chars
        ("password", "x" * 73),  # > 72 chars
        ("phone", "invalid#phone"),
    ],
)
def test_register_request_rejects_invalid(field: str, value: str) -> None:
    kwargs = dict(_BASE_REGISTER)
    kwargs[field] = value
    with pytest.raises(ValidationError):
        RegisterRequest(**kwargs)


# ── LoginRequest ─────────────────────────────────────────────────────────────


def test_login_request_valid() -> None:
    data = LoginRequest(email="USER@Example.COM", password="ValidPass1")
    assert data.email == "user@example.com"


@pytest.mark.parametrize(
    "field,value",
    [
        ("email", ""),
        ("email", "not-an-email"),
        ("password", ""),
        ("password", "x" * 73),
    ],
)
def test_login_request_rejects_invalid(field: str, value: str) -> None:
    kwargs = {"email": "test@example.com", "password": "ValidPass1"}
    kwargs[field] = value
    with pytest.raises(ValidationError):
        LoginRequest(**kwargs)


# ── AdminUserCreate ──────────────────────────────────────────────────────────


def test_admin_user_create_valid_citizen() -> None:
    data = AdminUserCreate(
        full_name="Citizen User",
        email="citizen@example.com",
        password="ValidPass1",
        role="CITIZEN",
    )
    assert data.department_id is None


def test_admin_user_create_valid_officer() -> None:
    data = AdminUserCreate(
        full_name="Officer User",
        email="officer@example.com",
        password="ValidPass1",
        role="DEPARTMENT_OFFICER",
        department_id=1,
    )
    assert data.department_id == 1


# ── AdminUserUpdate ──────────────────────────────────────────────────────────


def test_admin_user_update_partial() -> None:
    data = AdminUserUpdate(is_active=False)
    assert data.role is None
    assert data.department_id is None
    assert data.is_active is False


# ── PublicUser ───────────────────────────────────────────────────────────────


def test_public_user_excludes_password() -> None:
    user = PublicUser(
        id=1,
        full_name="Test User",
        email="test@example.com",
        role="CITIZEN",
        is_active=True,
    )
    assert not hasattr(user, "password")
    assert not hasattr(user, "password_hash")


# ── DepartmentOut ────────────────────────────────────────────────────────────


def test_department_out_valid() -> None:
    dept = DepartmentOut(id=1, name="Road Maintenance", code="ROADS")
    assert dept.id == 1
    assert dept.code == "ROADS"
