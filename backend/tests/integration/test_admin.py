"""
CivicTrack — Administration, Configuration & Audit Integration Tests (T-ADMIN, FR-046..FR-050, BR-15)
"""

from __future__ import annotations

from datetime import timedelta

from app.core.clock import utcnow
from app.models.audit import AuditLog
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.history import ComplaintStatusHistory
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

# ── TEST-027: Department & Category Deactivation Guards (FR-046, BR-15) ────────


def test_create_and_update_department(
    client: TestClient,
    admin_user: tuple[User, str],
) -> None:
    """FR-046: Admin can create and update departments."""
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create department
    payload = {
        "name": "Water and Sanitation",
        "code": "WATER_SAN",
        "description": "Clean water supply and drainage maintenance",
        "is_active": True,
    }
    resp = client.post("/api/v1/admin/departments", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Water and Sanitation"
    assert data["code"] == "WATER_SAN"
    assert data["is_active"] is True
    dept_id = data["id"]

    # 2. Duplicate name rejected with 409
    resp_dup = client.post("/api/v1/admin/departments", json=payload, headers=headers)
    assert resp_dup.status_code == 409
    assert resp_dup.json()["error"] == "DEPARTMENT_NAME_EXISTS"

    # 3. Update department
    update_payload = {"description": "Updated drainage description"}
    resp_update = client.patch(
        f"/api/v1/admin/departments/{dept_id}", json=update_payload, headers=headers
    )
    assert resp_update.status_code == 200
    assert resp_update.json()["description"] == "Updated drainage description"


def test_department_deactivation_blocked_by_active_categories(
    client: TestClient,
    admin_user: tuple[User, str],
    dept_roads: Department,
    cat_pothole: ComplaintCategory,
) -> None:
    """FR-046, BR-15: Cannot deactivate department with active categories (409 Conflict)."""
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    # Attempt to deactivate department while cat_pothole is active
    resp = client.patch(
        f"/api/v1/admin/departments/{dept_roads.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["error"] == "DEPARTMENT_IN_USE"
    assert body["details"]["active_categories"] >= 1


def test_department_deactivation_blocked_by_active_officers(
    client: TestClient,
    admin_user: tuple[User, str],
    db: Session,
    dept_roads: Department,
    cat_pothole: ComplaintCategory,
    officer_roads: tuple[User, str],
) -> None:
    """FR-046, BR-15: Cannot deactivate department with active officers (409 Conflict)."""
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    # Deactivate the category first so categories don't block
    cat_pothole.is_active = False
    db.commit()

    # Now attempt to deactivate department while officer_roads is active
    resp = client.patch(
        f"/api/v1/admin/departments/{dept_roads.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert resp.status_code == 409
    body = resp.json()
    assert body["error"] == "DEPARTMENT_IN_USE"
    assert body["details"]["active_officers"] >= 1

    # Deactivate the officer
    officer, _ = officer_roads
    officer.is_active = False
    db.commit()

    # Now deactivation succeeds
    resp_success = client.patch(
        f"/api/v1/admin/departments/{dept_roads.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert resp_success.status_code == 200
    assert resp_success.json()["is_active"] is False


def test_create_category_requires_active_department(
    client: TestClient,
    admin_user: tuple[User, str],
    db: Session,
) -> None:
    """FR-047, US-ADM-03: Creating category referencing inactive department fails with 422."""
    _, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    # Create an inactive department
    inactive_dept = Department(
        name="Defunct Department",
        code="DEFUNCT",
        description="Deprecated service",
        is_active=False,
    )
    db.add(inactive_dept)
    db.commit()

    payload = {
        "name": "Defunct Category",
        "code": "DEFUNCT_CAT",
        "description": "Category on defunct dept",
        "department_id": inactive_dept.id,
        "default_priority": "LOW",
        "is_active": True,
    }
    resp = client.post("/api/v1/admin/categories", json=payload, headers=headers)
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_DEPARTMENT"


# ── TEST-028: Category Remapping Semantics (FR-047, TRD §8.8) ─────────────────


def test_category_remap_preserves_existing_complaints(
    client: TestClient,
    admin_user: tuple[User, str],
    citizen_user: tuple[User, str],
    db: Session,
    dept_roads: Department,
    dept_electrical: Department,
) -> None:
    """
    FR-047, TRD §8.8, TEST-028:
    Remapping category to a new department updates the category and returns note,
    leaves existing complaint department unchanged, and new complaints route to new department.
    """
    _, token = admin_user
    citizen, _ = citizen_user
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create category initially mapped to dept_roads
    create_resp = client.post(
        "/api/v1/admin/categories",
        json={
            "name": "Traffic Signal Repair",
            "code": "TRAFFIC_SIGNAL",
            "department_id": dept_roads.id,
            "default_priority": "MEDIUM",
            "is_active": True,
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    cat_id = create_resp.json()["id"]

    # 2. Existing complaint created under dept_roads
    c1 = Complaint(
        complaint_number="CT-2026-000101",
        citizen_id=citizen.id,
        category_id=cat_id,
        department_id=dept_roads.id,
        title="Signal outage on Main Street",
        description="Signal is completely blank.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(c1)
    db.commit()
    db.refresh(c1)

    assert c1.department_id == dept_roads.id

    # 3. Remap category to dept_electrical
    remap_resp = client.patch(
        f"/api/v1/admin/categories/{cat_id}",
        json={"department_id": dept_electrical.id},
        headers=headers,
    )
    assert remap_resp.status_code == 200
    data = remap_resp.json()
    assert data["department"]["id"] == dept_electrical.id
    assert data["note"] == "Affects new complaints only."

    # 4. Existing complaint 1 retains historical department_id (dept_roads)
    db.refresh(c1)
    assert c1.department_id == dept_roads.id

    # 5. New complaint created using remapped category routes to dept_electrical
    category_in_db = db.get(ComplaintCategory, cat_id)
    assert category_in_db is not None
    c2 = Complaint(
        complaint_number="CT-2026-000102",
        citizen_id=citizen.id,
        category_id=cat_id,
        department_id=category_in_db.department_id,
        title="Second signal outage",
        description="Second signal failure.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(c2)
    db.commit()
    db.refresh(c2)

    assert c2.department_id == dept_electrical.id


# ── TEST-029: Audit Immutability & Filter Correctness (FR-049, FR-050) ────────


def test_audit_logs_query_and_filtering(
    client: TestClient,
    admin_user: tuple[User, str],
    citizen_user: tuple[User, str],
    db: Session,
) -> None:
    """FR-049: Platform Administrator can list and filter audit logs."""
    admin, token = admin_user
    citizen, _ = citizen_user
    headers = {"Authorization": f"Bearer {token}"}
    now = utcnow()

    # Create several audit logs
    a1 = AuditLog(
        actor_user_id=admin.id,
        actor_role=Role.PLATFORM_ADMIN.value,
        action="USER_CREATED",
        entity_type="USER",
        entity_id="99",
        metadata_json='{"email": "newofficer@demo.local"}',
        created_at=now - timedelta(days=2),
    )
    a2 = AuditLog(
        actor_user_id=citizen.id,
        actor_role=Role.CITIZEN.value,
        action="RBAC_DENIED",
        entity_type="ROUTE",
        entity_id="/api/v1/complaints/1/accept",
        metadata_json='{"method": "POST"}',
        created_at=now - timedelta(days=1),
    )
    a3 = AuditLog(
        actor_user_id=admin.id,
        actor_role=Role.PLATFORM_ADMIN.value,
        action="DEPARTMENT_CREATED",
        entity_type="DEPARTMENT",
        entity_id="10",
        metadata_json='{"name": "Health Dept"}',
        created_at=now,
    )
    db.add_all([a1, a2, a3])
    db.commit()

    # 1. List all audit logs
    resp = client.get("/api/v1/admin/audit-logs", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 3
    assert len(body["items"]) >= 3

    # 2. Filter by action
    resp_action = client.get("/api/v1/admin/audit-logs?action=RBAC_DENIED", headers=headers)
    assert resp_action.status_code == 200
    items = resp_action.json()["items"]
    assert len(items) >= 1
    assert all(item["action"] == "RBAC_DENIED" for item in items)

    # 3. Filter by actor_user_id
    resp_actor = client.get(f"/api/v1/admin/audit-logs?actor_user_id={citizen.id}", headers=headers)
    assert resp_actor.status_code == 200
    items = resp_actor.json()["items"]
    assert len(items) >= 1
    assert all(item["actor_user_id"] == citizen.id for item in items)

    # 4. Filter by entity_type
    resp_entity = client.get("/api/v1/admin/audit-logs?entity_type=DEPARTMENT", headers=headers)
    assert resp_entity.status_code == 200
    items = resp_entity.json()["items"]
    assert len(items) >= 1
    assert all(item["entity_type"] == "DEPARTMENT" for item in items)

    # 5. Filter by date range (from/to)
    from_str = (now - timedelta(hours=6)).isoformat()
    to_str = (now + timedelta(hours=1)).isoformat()
    resp_date = client.get(f"/api/v1/admin/audit-logs?from={from_str}&to={to_str}", headers=headers)
    assert resp_date.status_code == 200
    items = resp_date.json()["items"]
    assert any(item["action"] == "DEPARTMENT_CREATED" for item in items)


def test_audit_logs_immutability(
    client: TestClient,
    admin_user: tuple[User, str],
    db: Session,
) -> None:
    """
    FR-049, NFR-008, NFR-019:
    Audit logs cannot be updated or deleted via API (returns 405 Method Not Allowed or 404).
    """
    admin, token = admin_user
    headers = {"Authorization": f"Bearer {token}"}

    # Create an audit log
    audit = AuditLog(
        actor_user_id=admin.id,
        actor_role=Role.PLATFORM_ADMIN.value,
        action="TEST_ACTION",
        entity_type="SYSTEM",
        entity_id="1",
        metadata_json='{"immutable": true}',
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    audit_id = audit.id

    # Attempt PUT
    resp_put = client.put(
        f"/api/v1/admin/audit-logs/{audit_id}",
        json={"action": "TAMPERED"},
        headers=headers,
    )
    assert resp_put.status_code in [404, 405]

    # Attempt PATCH
    resp_patch = client.patch(
        f"/api/v1/admin/audit-logs/{audit_id}",
        json={"action": "TAMPERED"},
        headers=headers,
    )
    assert resp_patch.status_code in [404, 405]

    # Attempt DELETE
    resp_delete = client.delete(
        f"/api/v1/admin/audit-logs/{audit_id}",
        headers=headers,
    )
    assert resp_delete.status_code in [404, 405]

    # Verify record in DB is unchanged
    refreshed = db.get(AuditLog, audit_id)
    assert refreshed is not None
    assert refreshed.action == "TEST_ACTION"


# ── TEST-030: Activity Counts & Recent Events (FR-048, TRD §8.8) ───────────────


def test_platform_activity_counts_and_recent_events(
    client: TestClient,
    admin_user: tuple[User, str],
    citizen_user: tuple[User, str],
    officer_roads: tuple[User, str],
    db: Session,
    dept_roads: Department,
    cat_pothole: ComplaintCategory,
) -> None:
    """FR-048, TRD §8.8: Activity metrics aggregation and 20 recent timeline events."""
    _, token = admin_user
    citizen, _ = citizen_user
    officer, _ = officer_roads
    headers = {"Authorization": f"Bearer {token}"}
    now = utcnow()

    # 1. Create a submitted complaint
    c_sub = Complaint(
        complaint_number="CT-2026-000201",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Sub",
        description="Pothole description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    # 2. Create an in-progress complaint
    c_prog = Complaint(
        complaint_number="CT-2026-000202",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole In Prog",
        description="Pothole description.",
        status=Status.IN_PROGRESS,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(hours=12),
    )
    # 3. Create an escalated complaint
    c_esc = Complaint(
        complaint_number="CT-2026-000203",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Escalated",
        description="Pothole description.",
        status=Status.ESCALATED,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(days=8),
        escalated_at=now - timedelta(hours=1),
    )
    # 4. Create a resolved complaint
    c_res = Complaint(
        complaint_number="CT-2026-000204",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Resolved",
        description="Pothole description.",
        status=Status.RESOLVED,
        priority=Priority.LOW,
        accepted_at=now - timedelta(days=2),
        resolved_at=now - timedelta(hours=2),
        resolution_note="Road patched smoothly.",
    )
    db.add_all([c_sub, c_prog, c_esc, c_res])
    db.commit()

    # Add status history events
    h1 = ComplaintStatusHistory(
        complaint_id=c_sub.id,
        from_status=None,
        to_status=Status.SUBMITTED,
        actor_user_id=citizen.id,
        actor_role=Role.CITIZEN.value,
        note="Initial filing",
        created_at=now - timedelta(hours=20),
    )
    h2 = ComplaintStatusHistory(
        complaint_id=c_prog.id,
        from_status=Status.ACCEPTED,
        to_status=Status.IN_PROGRESS,
        actor_user_id=officer.id,
        actor_role=Role.DEPARTMENT_OFFICER.value,
        note="Work started",
        created_at=now - timedelta(hours=10),
    )
    h3 = ComplaintStatusHistory(
        complaint_id=c_esc.id,
        from_status=Status.IN_PROGRESS,
        to_status=Status.ESCALATED,
        actor_user_id=None,
        actor_role="SYSTEM",
        note="Auto escalation due to overdue deadline",
        created_at=now - timedelta(hours=1),
    )
    db.add_all([h1, h2, h3])
    db.commit()

    # Call GET /admin/activity
    resp = client.get("/api/v1/admin/activity", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # Check status counts
    assert data["by_status"]["SUBMITTED"] >= 1
    assert data["by_status"]["IN_PROGRESS"] >= 1
    assert data["by_status"]["ESCALATED"] >= 1
    assert data["by_status"]["RESOLVED"] >= 1

    # Check department summary for dept_roads
    roads_dept_entry = next((d for d in data["by_department"] if d["id"] == dept_roads.id), None)
    assert roads_dept_entry is not None
    # open complaints for roads: SUBMITTED + IN_PROGRESS + ESCALATED (not RESOLVED/REJECTED) >= 3
    assert roads_dept_entry["open"] >= 3
    assert roads_dept_entry["escalated"] >= 1

    # Check total escalations
    assert data["escalations_total"] >= 1
    assert data["escalation_window_minutes"] > 0
    assert "demo_mode" in data

    # Check recent events (<= 20, newest first)
    assert len(data["recent_events"]) <= 20
    assert len(data["recent_events"]) >= 3
    # Check that the most recent event is h3 (ESCALATED)
    first_event = data["recent_events"][0]
    assert first_event["complaint_number"] == c_esc.complaint_number
    assert first_event["to_status"] == Status.ESCALATED.value
    assert first_event["actor"] == "System"


# ── RBAC Authorization Tests ──────────────────────────────────────────────────


def test_non_admin_forbidden_on_admin_routes(
    client: TestClient,
    citizen_user: tuple[User, str],
    officer_roads: tuple[User, str],
) -> None:
    """Non-admin roles receive 403 Forbidden on all administration endpoints."""
    _, citizen_token = citizen_user
    _, officer_token = officer_roads

    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}
    officer_headers = {"Authorization": f"Bearer {officer_token}"}

    endpoints = [
        ("GET", "/api/v1/admin/departments"),
        ("POST", "/api/v1/admin/departments"),
        ("PATCH", "/api/v1/admin/departments/1"),
        ("GET", "/api/v1/admin/categories"),
        ("POST", "/api/v1/admin/categories"),
        ("PATCH", "/api/v1/admin/categories/1"),
        ("GET", "/api/v1/admin/activity"),
        ("GET", "/api/v1/admin/audit-logs"),
    ]

    for method, path in endpoints:
        if method == "GET":
            c_resp = client.get(path, headers=citizen_headers)
            o_resp = client.get(path, headers=officer_headers)
        elif method == "POST":
            c_resp = client.post(path, json={}, headers=citizen_headers)
            o_resp = client.post(path, json={}, headers=officer_headers)
        elif method == "PATCH":
            c_resp = client.patch(path, json={}, headers=citizen_headers)
            o_resp = client.patch(path, json={}, headers=officer_headers)

        assert c_resp.status_code == 403, (
            f"Citizen should get 403 on {method} {path}, got {c_resp.status_code}"
        )
        assert o_resp.status_code == 403, (
            f"Officer should get 403 on {method} {path}, got {o_resp.status_code}"
        )


def test_anonymous_unauthorized_on_admin_routes(client: TestClient) -> None:
    """Anonymous requests receive 401 Unauthorized."""
    resp = client.get("/api/v1/admin/activity")
    assert resp.status_code == 401
