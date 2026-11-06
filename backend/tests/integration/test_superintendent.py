"""
CivicTrack — Superintendent Oversight Integration Tests (T-SUP, FR-035..041, AC-09..AC-11)
"""

from __future__ import annotations

from datetime import timedelta

from app.core.clock import utcnow
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import OfficerActionType, Priority, Status
from app.models.history import ComplaintStatusHistory
from app.models.notification import Notification
from app.models.officer_action import OfficerAction
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

# ── TEST-024: Queue ordering & overdue computation (FR-035, AC-09) ─────────────


def test_escalation_queue_ordering_and_overdue(
    client: TestClient,
    db: Session,
    superintendent_user: tuple[User, str],
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """FR-035, AC-09: Queue shows escalated complaints ordered by overdue duration desc."""
    _, token = superintendent_user
    citizen, _ = citizen_user
    now = utcnow()

    # Create complaint 1: overdue by 2 hours
    c1 = Complaint(
        complaint_number="CT-2026-000010",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole 2h overdue",
        description="Pothole description long enough.",
        status=Status.ESCALATED,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(days=7, hours=2),
        sla_seconds=604800,
        resolution_due_at=now - timedelta(hours=2),
        escalated_at=now - timedelta(hours=2),
    )

    # Create complaint 2: overdue by 10 hours (should appear first)
    c2 = Complaint(
        complaint_number="CT-2026-000020",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole 10h overdue",
        description="Pothole description long enough.",
        status=Status.ESCALATED,
        priority=Priority.HIGH,
        accepted_at=now - timedelta(days=7, hours=10),
        sla_seconds=604800,
        resolution_due_at=now - timedelta(hours=10),
        escalated_at=now - timedelta(hours=10),
    )

    # Create complaint 3: non-escalated (must not appear in queue)
    c3 = Complaint(
        complaint_number="CT-2026-000030",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole in progress",
        description="Pothole description long enough.",
        status=Status.IN_PROGRESS,
        priority=Priority.MEDIUM,
    )

    db.add_all([c1, c2, c3])
    db.commit()

    res = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total"] >= 2
    assert data["summary"]["open"] >= 2
    assert data["summary"]["oldest_overdue_seconds"] >= 36000  # >= 10h in seconds

    items = data["items"]
    # Check ordering: complaint 2 (10h overdue) must precede complaint 1 (2h overdue)
    item_numbers = [item["complaint_number"] for item in items]
    assert "CT-2026-000020" in item_numbers
    assert "CT-2026-000010" in item_numbers
    assert "CT-2026-000030" not in item_numbers  # Non-escalated excluded

    idx_c2 = item_numbers.index("CT-2026-000020")
    idx_c1 = item_numbers.index("CT-2026-000010")
    assert idx_c2 < idx_c1

    # Verify field structure
    item = items[idx_c2]
    assert item["department"]["name"] == "Road Maintenance"
    assert (
        item["current_overdue_seconds"] >= item["overdue_seconds"]
        or item["current_overdue_seconds"] > 0
    )
    assert item["status"] == "ESCALATED"


def test_escalation_summary_endpoint(
    client: TestClient,
    superintendent_user: tuple[User, str],
) -> None:
    """FR-035: GET /superintendent/summary returns metric overview."""
    _, token = superintendent_user
    res = client.get(
        "/api/v1/superintendent/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "open" in data
    assert "oldest_overdue_seconds" in data


# ── TEST-025: Supervisory action, timeline entry & NT-06 fan-out (FR-038, AC-10) ─


def test_record_superintendent_action_and_notifications(
    client: TestClient,
    db: Session,
    superintendent_user: tuple[User, str],
    citizen_user: tuple[User, str],
    officer_roads: tuple[User, str],
    dept_electrical: Department,
    escalated_complaint: Complaint,
) -> None:
    """FR-038, FR-039, AC-10: Record action, append row, timeline entry, NT-06 fan-out."""
    sup_user, token = superintendent_user
    citizen, _ = citizen_user
    officer, _ = officer_roads

    payload = {
        "action_type": "FOLLOW_UP",
        "note": "Complete the road repair within 24 hours.",
        "directed_department_id": dept_electrical.id,
    }

    res = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 201
    data = res.json()

    assert data["action_type"] == "FOLLOW_UP"
    assert data["note"] == "Complete the road repair within 24 hours."
    assert data["directed_department"]["id"] == dept_electrical.id
    assert data["officer"]["id"] == sup_user.id
    assert "NT-06" in data["notifications_created"]

    # Verify complaint original department is preserved (FR-039)
    db.refresh(escalated_complaint)
    assert escalated_complaint.department_id != dept_electrical.id
    assert escalated_complaint.status == Status.ESCALATED  # Status remains unchanged

    # Verify action row in database
    action = db.execute(
        select(OfficerAction).where(OfficerAction.complaint_id == escalated_complaint.id)
    ).scalar_one_or_none()
    assert action is not None
    assert action.action_type == OfficerActionType.FOLLOW_UP
    assert action.officer_user_id == sup_user.id

    # Verify NT-06 notifications generated
    notifications = (
        db.execute(
            select(Notification).where(
                Notification.complaint_id == escalated_complaint.id,
                Notification.trigger_code == "NT-06",
            )
        )
        .scalars()
        .all()
    )

    recipient_ids = {n.recipient_user_id for n in notifications}
    assert citizen.id in recipient_ids  # Citizen owner notified
    assert officer.id in recipient_ids  # Responsible department officer notified

    # Verify timeline entry
    res_timeline = client.get(
        f"/api/v1/complaints/{escalated_complaint.id}/timeline",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_timeline.status_code == 200
    timeline = res_timeline.json()
    assert any(event["event_type"] == "SUPERINTENDENT_FOLLOW_UP" for event in timeline)


def test_action_validation_errors(
    client: TestClient,
    superintendent_user: tuple[User, str],
    escalated_complaint: Complaint,
) -> None:
    """FR-038: Validation for note length (5-2000) and directed department."""
    _, token = superintendent_user

    # Note too short (< 5 chars)
    r1 = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
        json={"action_type": "INSTRUCTION", "note": "Tiny"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 422

    # Invalid directed department
    r2 = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
        json={
            "action_type": "INSTRUCTION",
            "note": "Valid instruction note.",
            "directed_department_id": 999999,
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 422


# ── TEST-026: Superintendent resolution & scope guards (FR-041, AC-11) ──────────


def test_superintendent_resolve_escalated_complaint(
    client: TestClient,
    db: Session,
    superintendent_user: tuple[User, str],
    citizen_user: tuple[User, str],
    escalated_complaint: Complaint,
) -> None:
    """FR-041, AC-11: Resolve escalated complaint, history, NT-07, and queue exit."""
    sup_user, token = superintendent_user
    citizen, _ = citizen_user

    res = client.post(
        f"/api/v1/complaints/{escalated_complaint.id}/resolve",
        json={"note": "Issue inspected and verified fixed by municipal contractor."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "RESOLVED"
    assert data["resolved_by"]["id"] == sup_user.id
    assert "NT-07" in data["notifications_created"]

    # Verify DB state
    db.refresh(escalated_complaint)
    assert escalated_complaint.status == Status.RESOLVED
    assert escalated_complaint.resolved_by_user_id == sup_user.id

    # Verify status history row
    history = db.execute(
        select(ComplaintStatusHistory).where(
            ComplaintStatusHistory.complaint_id == escalated_complaint.id,
            ComplaintStatusHistory.to_status == Status.RESOLVED,
        )
    ).scalar_one_or_none()
    assert history is not None
    assert history.actor_user_id == sup_user.id
    assert history.from_status == Status.ESCALATED

    # Verify NT-07 notification for citizen
    notif = db.execute(
        select(Notification).where(
            Notification.complaint_id == escalated_complaint.id,
            Notification.trigger_code == "NT-07",
        )
    ).scalar_one_or_none()
    assert notif is not None
    assert notif.recipient_user_id == citizen.id

    # Verify complaint leaves the escalation queue
    res_queue = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    queue_numbers = [item["complaint_number"] for item in res_queue.json()["items"]]
    assert escalated_complaint.complaint_number not in queue_numbers


def test_superintendent_action_on_non_escalated_returns_409(
    client: TestClient,
    superintendent_user: tuple[User, str],
    complaint_roads: Complaint,
) -> None:
    """RBAC-05, FR-037: Action on non-escalated complaint rejected with 409."""
    _, token = superintendent_user

    # complaint_roads is PENDING_DEPARTMENT_REVIEW
    res_action = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/superintendent-actions",
        json={"action_type": "NOTE", "note": "Superintendent note attempt."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_action.status_code == 409
    assert res_action.json()["error"] == "INVALID_TRANSITION"

    res_resolve = client.post(
        f"/api/v1/complaints/{complaint_roads.id}/resolve",
        json={"note": "Premature resolution attempt."},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_resolve.status_code == 409
    assert res_resolve.json()["error"] == "INVALID_TRANSITION"


def test_superintendent_can_read_any_complaint_for_oversight(
    client: TestClient,
    superintendent_user: tuple[User, str],
    complaint_roads: Complaint,
    complaint_electrical: Complaint,
) -> None:
    """FR-037, BR-09: Superintendent has read oversight on all complaints."""
    _, token = superintendent_user

    # Read Roads complaint (pending)
    r1 = client.get(
        f"/api/v1/complaints/{complaint_roads.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r1.status_code == 200
    assert r1.json()["id"] == complaint_roads.id

    # Read Electrical complaint (accepted)
    r2 = client.get(
        f"/api/v1/complaints/{complaint_electrical.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert r2.json()["id"] == complaint_electrical.id


def test_non_superintendent_forbidden(
    client: TestClient,
    citizen_user: tuple[User, str],
    officer_roads: tuple[User, str],
    escalated_complaint: Complaint,
) -> None:
    """AC-13, RBAC-01: Citizen and Officer forbidden from superintendent endpoints (403)."""
    _, cit_token = citizen_user
    _, off_token = officer_roads

    # Citizen accessing queue -> 403
    assert (
        client.get(
            "/api/v1/superintendent/escalations",
            headers={"Authorization": f"Bearer {cit_token}"},
        ).status_code
        == 403
    )

    # Department Officer attempting supervisory action -> 403
    assert (
        client.post(
            f"/api/v1/complaints/{escalated_complaint.id}/superintendent-actions",
            json={"action_type": "NOTE", "note": "Officer attempt"},
            headers={"Authorization": f"Bearer {off_token}"},
        ).status_code
        == 403
    )
