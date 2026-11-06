"""
CivicTrack — Complaints Integration Tests (FR-015..024, AC-02, AC-04)

Tests complaint retrieval, acceptance, rejection, and resolution endpoints
with role-based access control.
"""

from __future__ import annotations

from app.models.complaint import Complaint
from app.models.enums import Role, Status
from fastapi.testclient import TestClient

# ── GET /complaints/{id} ─────────────────────────────────────────────────────


def test_get_complaint_owner(
    client: TestClient, citizen_user: tuple, complaint_roads: Complaint
) -> None:
    """FR-015: Citizen can read their own complaint."""
    _, token = citizen_user
    res = client.get(
        f"/api/v1/complaints/{complaint_roads.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == complaint_roads.id
    assert data["complaint_number"] == complaint_roads.complaint_number
    assert data["status"] == Status.PENDING_DEPARTMENT_REVIEW.value


def test_get_complaint_foreign_citizen_403(
    client: TestClient, citizen_user: tuple, complaint_electrical: Complaint, db
) -> None:
    """RBAC-03: Citizen cannot read another citizen's complaint."""
    # Create a second citizen who does not own complaint_electrical
    from app.core.security import hash_password
    from app.models.user import User

    other = User(
        full_name="Other Citizen",
        email="other.citizen@example.com",
        password_hash=hash_password("OtherPass123"),
        role=Role.CITIZEN,
        is_active=True,
    )
    db.add(other)
    db.commit()
    db.refresh(other)
    from app.core.security import create_access_token

    token, _ = create_access_token(other.id, other.role.value)

    res = client.get(
        f"/api/v1/complaints/{complaint_electrical.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_get_complaint_officer_same_department(
    client: TestClient, officer_roads: tuple, complaint_roads: Complaint
) -> None:
    """RBAC-02: Department officer can read complaints in their department."""
    _, token = officer_roads
    res = client.get(
        f"/api/v1/complaints/{complaint_roads.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200


def test_get_complaint_officer_other_department_403(
    client: TestClient, officer_electrical: tuple, complaint_roads: Complaint
) -> None:
    """RBAC-02: Department officer cannot read another department's complaint."""
    _, token = officer_electrical
    res = client.get(
        f"/api/v1/complaints/{complaint_roads.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_get_complaint_not_found(client: TestClient, citizen_user: tuple) -> None:
    """FR-015: Unknown complaint returns 404."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/complaints/999999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


def test_get_complaint_anonymous_401(client: TestClient, complaint_roads: Complaint) -> None:
    """RBAC-01: Anonymous access returns 401."""
    res = client.get(f"/api/v1/complaints/{complaint_roads.id}")
    assert res.status_code == 401


# ── POST /complaints/{id}/accept ─────────────────────────────────────────────


def test_accept_complaint_officer(
    client: TestClient, officer_roads: tuple, complaint_roads: Complaint
) -> None:
    """FR-019: Department officer accepts complaint in their department."""
    _, token = officer_roads
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "ACCEPTED"


def test_accept_complaint_citizen_403(
    client: TestClient, citizen_user: tuple, complaint_roads: Complaint
) -> None:
    """FR-019: Citizen cannot accept a complaint."""
    _, token = citizen_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_accept_complaint_officer_other_dept_403(
    client: TestClient, officer_electrical: tuple, complaint_roads: Complaint
) -> None:
    """RBAC-02: Officer cannot accept another department's complaint."""
    _, token = officer_electrical
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# ── POST /complaints/{id}/reject ─────────────────────────────────────────────


def test_reject_complaint_officer(
    client: TestClient, officer_roads: tuple, complaint_roads: Complaint
) -> None:
    """FR-020: Department officer rejects complaint in their department."""
    _, token = officer_roads
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"


def test_reject_complaint_citizen_403(
    client: TestClient, citizen_user: tuple, complaint_roads: Complaint
) -> None:
    """FR-020: Citizen cannot reject a complaint."""
    _, token = citizen_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# ── POST /complaints/{id}/resolve ────────────────────────────────────────────


def test_resolve_complaint_officer(
    client: TestClient, officer_roads: tuple, complaint_roads: Complaint
) -> None:
    """FR-024: Department officer resolves complaint in their department."""
    _, token = officer_roads
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "RESOLVED"


def test_resolve_complaint_superintendent(
    client: TestClient, superintendent_user: tuple, escalated_complaint: Complaint
) -> None:
    """FR-041: Superintendent resolves escalated complaint."""
    _, token = superintendent_user
    res = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "RESOLVED"


def test_resolve_complaint_superintendent_non_escalated_409(
    client: TestClient, superintendent_user: tuple, complaint_roads: Complaint
) -> None:
    """RBAC-05: Superintendent cannot act on non-escalated complaint."""
    _, token = superintendent_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 409
    assert res.json()["error"] == "INVALID_TRANSITION"


def test_resolve_complaint_officer_other_dept_403(
    client: TestClient, officer_electrical: tuple, complaint_roads: Complaint
) -> None:
    """RBAC-02: Officer cannot resolve another department's complaint."""
    _, token = officer_electrical
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# ── POST /complaints/{id}/superintendent-actions ─────────────────────────────


def test_superintendent_action(
    client: TestClient, superintendent_user: tuple, escalated_complaint: Complaint
) -> None:
    """FR-038: Superintendent records action on escalated complaint."""
    _, token = superintendent_user
    res = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    assert res.json()["status"] == "ACTION_RECORDED"


def test_superintendent_action_officer_403(
    client: TestClient, officer_roads: tuple, escalated_complaint: Complaint
) -> None:
    """RBAC-01: Department officer cannot record superintendent action."""
    _, token = officer_roads
    res = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


# ── Role type for fixture unpacking ──────────────────────────────────────────


# The conftest fixtures return tuple[User, str]; we access by index.
