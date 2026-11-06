"""
CivicTrack — RBAC 12-Case Matrix and User Administration Tests (T-RBAC, T-INT-15, T-INT-18, FR-004, FR-006)
"""

from __future__ import annotations

from app.models.audit import AuditLog
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# ── 12-Case RBAC Matrix (TRD §9.7, T-INT-15) ───────────────────────────────────


def test_rbac_case_1_citizen_cannot_accept(
    client: TestClient, citizen_user: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 1: Citizen POST /complaints/{id}/accept -> 403."""
    _, token = citizen_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_2_citizen_cannot_reject(
    client: TestClient, citizen_user: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 2: Citizen POST /complaints/{id}/reject -> 403."""
    _, token = citizen_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_3_citizen_cannot_view_department_queue(
    client: TestClient, citizen_user: tuple[User, str]
) -> None:
    """Case 3: Citizen GET /department/complaints -> 403."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/department/complaints",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_4_citizen_cannot_view_superintendent_escalations(
    client: TestClient, citizen_user: tuple[User, str]
) -> None:
    """Case 4: Citizen GET /superintendent/escalations -> 403."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_5_citizen_cannot_access_admin_users(
    client: TestClient, citizen_user: tuple[User, str]
) -> None:
    """Case 5: Citizen GET /admin/users -> 403."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_6_officer_cannot_read_other_department_complaint(
    client: TestClient, officer_electrical: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 6: Department Officer read another department's complaint -> 403."""
    _, token = officer_electrical
    res = client.get(
        f"/api/v1/complaints/{complaint_roads.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_7_officer_cannot_accept_other_department_complaint(
    client: TestClient, officer_electrical: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 7: Department Officer accept another department's complaint -> 403."""
    _, token = officer_electrical
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_8_officer_cannot_record_superintendent_action(
    client: TestClient, officer_roads: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 8: Department Officer POST /complaints/{id}/superintendent-actions -> 403."""
    _, token = officer_roads
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/superintendent-actions",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_9_superintendent_cannot_create_categories(
    client: TestClient, superintendent_user: tuple[User, str]
) -> None:
    """Case 9: Superintendent POST /admin/categories -> 403."""
    _, token = superintendent_user
    res = client.post(
        "/api/v1/admin/categories",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_10_admin_cannot_accept_complaint(
    client: TestClient, admin_user: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 10: Administrator POST /complaints/{id}/accept -> 403 (no operational permission)."""
    _, token = admin_user
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/accept",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_11_officer_cannot_resolve_other_department_complaint(
    client: TestClient, officer_electrical: tuple[User, str], complaint_roads: Complaint
) -> None:
    """Case 11: Department Officer resolve another department's complaint -> 403."""
    _, token = officer_electrical
    res = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/resolve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "FORBIDDEN"


def test_rbac_case_12_anonymous_rejected(client: TestClient, complaint_roads: Complaint) -> None:
    """Case 12: Anonymous on any protected route -> 401."""
    res1 = client.get(f"/api/v1/complaints/{complaint_roads.id}")
    assert res1.status_code == 401

    res2 = client.get("/api/v1/admin/users")
    assert res2.status_code == 401

    res3 = client.get("/api/v1/department/complaints")
    assert res3.status_code == 401


# ── RBAC Audit Log (RBAC-08) ───────────────────────────────────────────────────


def test_rbac_denial_creates_audit_log(
    client: TestClient, db: Session, citizen_user: tuple[User, str]
) -> None:
    """RBAC-08: Denied attempts produce an audit entry with actor, route, method."""
    user, token = citizen_user
    client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {token}"},
    )

    audit = db.execute(
        select(AuditLog).where(
            AuditLog.actor_user_id == user.id,
            AuditLog.action == "RBAC_DENIED",
        )
    ).scalar_one_or_none()

    assert audit is not None
    assert audit.actor_role == "CITIZEN"
    assert "/admin/users" in (audit.entity_id or "")


# ── Administrator User Management & Last Admin Guard (FR-006, T-INT-18) ────────


def test_admin_list_users(client: TestClient, admin_user: tuple[User, str]) -> None:
    """FR-006: Admin lists users with pagination."""
    _, token = admin_user
    res = client.get(
        "/api/v1/admin/users?page=1&page_size=10",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1
    assert data["page"] == 1


def test_admin_create_officer_with_department(
    client: TestClient, admin_user: tuple[User, str], dept_roads: Department
) -> None:
    """FR-006: Admin creates Department Officer with required active department."""
    _, token = admin_user
    payload = {
        "full_name": "New Officer",
        "email": "new.officer@demo.local",
        "password": "OfficerPassword123",
        "role": "DEPARTMENT_OFFICER",
        "department_id": dept_roads.id,
        "is_active": True,
    }
    res = client.post(
        "/api/v1/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == "new.officer@demo.local"
    assert data["role"] == "DEPARTMENT_OFFICER"
    assert data["department"]["id"] == dept_roads.id


def test_admin_create_officer_without_department_fails(
    client: TestClient, admin_user: tuple[User, str]
) -> None:
    """FR-006: Officer without department is rejected with 422."""
    _, token = admin_user
    payload = {
        "full_name": "Officer No Dept",
        "email": "nodept@demo.local",
        "password": "OfficerPassword123",
        "role": "DEPARTMENT_OFFICER",
        "department_id": None,
    }
    res = client.post(
        "/api/v1/admin/users",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 422


def test_last_admin_protection(client: TestClient, admin_user: tuple[User, str]) -> None:
    """FR-006, T-INT-18: Cannot deactivate or demote the last active Platform Administrator (409)."""
    user, token = admin_user

    # Attempt to deactivate the only active admin
    res_deact = client.patch(
        f"/api/v1/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_deact.status_code == 409
    assert res_deact.json()["error"] == "LAST_ADMIN_PROTECTED"

    # Attempt to demote the only active admin
    res_demote = client.patch(
        f"/api/v1/admin/users/{user.id}",
        json={"role": "CITIZEN"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_demote.status_code == 409
    assert res_demote.json()["error"] == "LAST_ADMIN_PROTECTED"

    # Create a second admin
    res_create = client.post(
        "/api/v1/admin/users",
        json={
            "full_name": "Second Admin",
            "email": "admin2@demo.local",
            "password": "AdminPassword123",
            "role": "PLATFORM_ADMIN",
            "is_active": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_create.status_code == 201
    second_admin_id = res_create.json()["id"]
    assert second_admin_id > 0

    # Now deactivating the first admin succeeds
    res_deact_ok = client.patch(
        f"/api/v1/admin/users/{user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_deact_ok.status_code == 200
    assert res_deact_ok.json()["is_active"] is False


def test_concurrent_last_admin_protection(client: TestClient, admin_user: tuple[User, str]) -> None:
    """TEST-004: Concurrency test proving concurrent requests cannot deactivate the last active admin."""
    from concurrent.futures import ThreadPoolExecutor

    user, token = admin_user

    def attempt_deactivate() -> int:
        res = client.patch(
            f"/api/v1/admin/users/{user.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        return res.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_deactivate)
        f2 = executor.submit(attempt_deactivate)
        status_codes = [f1.result(), f2.result()]

    # Since there was only 1 active admin, both requests must be blocked with 409
    assert all(code == 409 for code in status_codes)
