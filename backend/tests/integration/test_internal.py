"""Internal escalation endpoints (BE-075, BE-076, FR-034)."""

from __future__ import annotations

from datetime import timedelta

from app.core.clock import utcnow
from app.core.config import settings
from app.models.complaint import Complaint
from app.models.enums import Status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

AUTH = {"X-Internal-Token": settings.internal_trigger_token}


def _make_overdue(db: Session, complaint: Complaint) -> Complaint:
    complaint.status = Status.ACCEPTED
    complaint.accepted_at = utcnow() - timedelta(days=8)
    complaint.resolution_due_at = utcnow() - timedelta(hours=1)
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def test_internal_trigger_requires_token(client: TestClient) -> None:
    res = client.post("/api/v1/internal/escalations/run")
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_INTERNAL_TOKEN"


def test_internal_trigger_escalates_once(
    client: TestClient, db: Session, complaint_electrical: Complaint
) -> None:
    complaint = _make_overdue(db, complaint_electrical)

    first = client.post("/api/v1/internal/escalations/run", headers=AUTH)
    assert first.status_code == 200
    assert first.json() == {"evaluated": 1, "escalated": 1, "skipped": 0}

    db.refresh(complaint)
    assert complaint.status == Status.ESCALATED

    second = client.post("/api/v1/internal/escalations/trigger", headers=AUTH)
    assert second.status_code == 200
    assert second.json() == {"evaluated": 0, "escalated": 0, "skipped": 0}


def test_internal_status_reports_configuration(client: TestClient) -> None:
    res = client.get("/api/v1/internal/escalation-status", headers=AUTH)
    assert res.status_code == 200
    body = res.json()
    assert body["effective_window_minutes"] == settings.escalation_window_minutes
    assert body["check_interval_seconds"] == settings.escalation_check_seconds
    assert "last_escalation_at" in body
