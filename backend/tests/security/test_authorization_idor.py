"""
CivicTrack — Security Test Suite: Authorization & IDOR Probes (TEST-050, SEC-05, SEC-10, NFR-005, NFR-007)
"""

from __future__ import annotations

from app.core.security import hash_password
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_idor_citizen_cannot_read_another_citizens_complaint(
    client: TestClient,
    db: Session,
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    citizen_user: tuple[User, str],
) -> None:
    """TEST-050, SEC-10, NFR-005: Citizen A cannot view Citizen B's complaint (IDOR probe)."""
    citizen_a, token_a = citizen_user

    # Create Citizen B
    citizen_b = User(
        full_name="Citizen Bob",
        email="bob@demo.local",
        password_hash=hash_password("CitizenBob123"),
        role=Role.CITIZEN,
        is_active=True,
    )
    db.add(citizen_b)
    db.commit()

    # Create Complaint owned by Citizen B
    comp_b = Complaint(
        complaint_number="CT-2026-000888",
        citizen_id=citizen_b.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Bob's Private Pothole Issue",
        description="Private description with location.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(comp_b)
    db.commit()
    db.refresh(comp_b)

    # Citizen A attempts to read Citizen B's complaint
    headers_a = {"Authorization": f"Bearer {token_a}"}
    resp = client.get(f"/api/v1/complaints/{comp_b.id}", headers=headers_a)
    assert resp.status_code == 403
    assert resp.json()["error"] == "FORBIDDEN"

    # Citizen A attempts to read Citizen B's timeline
    resp_timeline = client.get(f"/api/v1/complaints/{comp_b.id}/timeline", headers=headers_a)
    assert resp_timeline.status_code == 403


def test_idor_officer_cannot_access_or_act_on_foreign_department(
    client: TestClient,
    db: Session,
    cat_streetlight: ComplaintCategory,
    dept_electrical: Department,
    officer_roads: tuple[User, str],
    citizen_user: tuple[User, str],
) -> None:
    """TEST-050, SEC-10, AC-14: Roads officer cannot inspect, accept, or resolve Electrical complaint."""
    _, roads_token = officer_roads
    citizen, _ = citizen_user
    roads_headers = {"Authorization": f"Bearer {roads_token}"}

    # Complaint assigned to Electrical Department
    comp_elec = Complaint(
        complaint_number="CT-2026-000999",
        citizen_id=citizen.id,
        category_id=cat_streetlight.id,
        department_id=dept_electrical.id,
        title="Flickering High Voltage Line",
        description="Electrical complaint description.",
        status=Status.SUBMITTED,
        priority=Priority.HIGH,
    )
    db.add(comp_elec)
    db.commit()
    db.refresh(comp_elec)

    # 1. Detail probe -> 403
    resp_get = client.get(f"/api/v1/complaints/{comp_elec.id}", headers=roads_headers)
    assert resp_get.status_code == 403

    # 2. Accept probe -> 403
    resp_accept = client.post(f"/api/v1/complaints/{comp_elec.id}/accept", headers=roads_headers)
    assert resp_accept.status_code == 403

    # 3. Reject probe -> 403
    resp_reject = client.post(
        f"/api/v1/complaints/{comp_elec.id}/reject",
        json={"reason": "Not our issue"},
        headers=roads_headers,
    )
    assert resp_reject.status_code == 403

    # 4. Resolve probe -> 403
    resp_resolve = client.post(
        f"/api/v1/complaints/{comp_elec.id}/resolve",
        json={"note": "Fixed by roads department improperly"},
        headers=roads_headers,
    )
    assert resp_resolve.status_code == 403


def test_mass_assignment_prevented_on_registration(client: TestClient) -> None:
    """TEST-050: Public registration ignores client-supplied privileged role or active flags."""
    payload = {
        "full_name": "Attacker Trying Privilege Escalation",
        "email": "attacker@demo.local",
        "password": "Password123",
        "role": "PLATFORM_ADMIN",
        "department_id": 1,
        "is_active": True,
    }
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 201
    user_data = resp.json()["user"]
    # Role must strictly be CITIZEN
    assert user_data["role"] == Role.CITIZEN.value
    assert user_data["department"] is None


def test_sql_injection_resistance(
    client: TestClient,
    admin_user: tuple[User, str],
) -> None:
    """TEST-050, SEC-07: SQL injection probes in parameters are safely escaped and return cleanly."""
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    payloads = [
        "' OR '1'='1",
        "1; DROP TABLE users; --",
        "' UNION SELECT * FROM users --",
    ]

    for p in payloads:
        # Audit logs filter probe
        resp = client.get(f"/api/v1/admin/audit-logs?action={p}", headers=headers)
        assert resp.status_code == 200
        # No error, returns empty or matching without syntax exception
        assert "items" in resp.json()

        # Department list filter probe
        resp_dept = client.get(f"/api/v1/admin/departments?name={p}", headers=headers)
        assert resp_dept.status_code == 200
