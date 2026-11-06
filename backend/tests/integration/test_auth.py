"""
CivicTrack — Authentication Integration Tests (T-AUTH, FR-001..003, FR-005, AC-01)
"""

from __future__ import annotations

from datetime import timedelta

from app.core.security import create_access_token
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_register_citizen_success(client: TestClient) -> None:
    """FR-001, AC-01: Visitor registers Citizen account and receives JWT + profile."""
    payload = {
        "full_name": "Priya Sharma",
        "email": "priya.sharma@example.com",
        "password": "CitizenPassword123",
        "phone": "+91 98765 43210",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 28800  # 8 hours

    user = data["user"]
    assert user["full_name"] == "Priya Sharma"
    assert user["email"] == "priya.sharma@example.com"
    assert user["role"] == "CITIZEN"
    assert user["is_active"] is True
    assert user["department"] is None
    assert "password" not in user
    assert "password_hash" not in user


def test_register_duplicate_email_conflict(client: TestClient) -> None:
    """FR-001: Duplicate email returns 409 EMAIL_ALREADY_REGISTERED case-insensitively."""
    payload = {
        "full_name": "Priya Sharma",
        "email": "unique.citizen@example.com",
        "password": "CitizenPassword123",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    # Attempt registration with uppercase variant
    payload_upper = {
        "full_name": "Another Name",
        "email": "UNIQUE.CITIZEN@EXAMPLE.COM",
        "password": "CitizenPassword123",
    }
    res2 = client.post("/api/v1/auth/register", json=payload_upper)
    assert res2.status_code == 409
    assert res2.json()["error"] == "EMAIL_ALREADY_REGISTERED"


def test_register_password_policy_validation(client: TestClient) -> None:
    """FR-001, NFR-004: Password 8-72 chars with at least one letter and one digit."""
    # Too short (< 8 chars)
    r1 = client.post(
        "/api/v1/auth/register",
        json={"full_name": "User", "email": "u1@example.com", "password": "Pass1"},
    )
    assert r1.status_code == 422

    # No digits
    r2 = client.post(
        "/api/v1/auth/register",
        json={"full_name": "User", "email": "u2@example.com", "password": "NoDigitsPassword"},
    )
    assert r2.status_code == 422

    # No letters
    r3 = client.post(
        "/api/v1/auth/register",
        json={"full_name": "User", "email": "u3@example.com", "password": "1234567890"},
    )
    assert r3.status_code == 422

    # Invalid phone
    r4 = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "User",
            "email": "u4@example.com",
            "password": "ValidPassword1",
            "phone": "invalid#phone",
        },
    )
    assert r4.status_code == 422


def test_login_success(client: TestClient) -> None:
    """FR-002: Authenticate active user with email and password."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rohan Verma",
            "email": "rohan@example.com",
            "password": "Password123",
        },
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ROHAN@example.com", "password": "Password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "rohan@example.com"


def test_login_invalid_password_returns_401(client: TestClient) -> None:
    """FR-002: Incorrect password returns 401 with generic message."""
    client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "User Test",
            "email": "test.pwd@example.com",
            "password": "ValidPassword1",
        },
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "test.pwd@example.com", "password": "WrongPassword1"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password."
    assert response.json()["error"] == "INVALID_CREDENTIALS"


def test_login_nonexistent_email_returns_401(client: TestClient) -> None:
    """FR-002: Nonexistent user returns 401 with identical generic message."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "does.not.exist@example.com", "password": "SomePassword1"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password."
    assert response.json()["error"] == "INVALID_CREDENTIALS"


def test_login_inactive_user_returns_identical_401(client: TestClient, db: Session) -> None:
    """FR-002: Inactive user returns 401 with identical generic message."""
    reg = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Inactive User",
            "email": "inactive@example.com",
            "password": "Password123",
        },
    )
    user_id = reg.json()["user"]["id"]

    # Deactivate user directly in DB
    user = db.get(User, user_id)
    assert user is not None
    user.is_active = False
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "inactive@example.com", "password": "Password123"},
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Invalid email or password."


def test_logout_returns_204(client: TestClient) -> None:
    """FR-002: Logout returns 204."""
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 204


def test_get_me_success(client: TestClient, officer_roads: tuple[User, str]) -> None:
    """FR-005: Read own profile including department when applicable."""
    _, token = officer_roads

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "roads@demo.local"
    assert data["role"] == "DEPARTMENT_OFFICER"
    assert data["department"] is not None
    assert data["department"]["code"] == "ROADS"
    assert "password" not in data
    assert "password_hash" not in data


def test_get_me_unauthorized_without_token(client: TestClient) -> None:
    """RBAC-01: Missing token returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"] == "UNAUTHORIZED"


def test_expired_token_rejected(client: TestClient, citizen_user: tuple[User, str]) -> None:
    """NFR-006: Expired token rejected with 401 TOKEN_EXPIRED."""
    user, _ = citizen_user
    expired_token, _ = create_access_token(
        user_id=user.id,
        role=user.role.value,
        expires_delta=timedelta(seconds=-10),
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "TOKEN_EXPIRED"


def test_deactivated_user_token_rejected(
    client: TestClient, db: Session, citizen_user: tuple[User, str]
) -> None:
    """RBAC-06: Deactivated user rejected on next request even with valid JWT."""
    user, token = citizen_user

    # Deactivate user in DB
    u = db.get(User, user.id)
    assert u is not None
    u.is_active = False
    db.commit()

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert response.json()["error"] == "INACTIVE_ACCOUNT"
