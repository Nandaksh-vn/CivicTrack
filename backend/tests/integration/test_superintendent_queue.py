"""
CivicTrack — Superintendent Queue Integration Tests (FR-035, TRD §8.6)

Tests the superintendent escalation queue endpoint.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_superintendent_escalations_superintendent(
    client: TestClient, superintendent_user: tuple
) -> None:
    """FR-035: Superintendent can view escalation queue."""
    _, token = superintendent_user
    res = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["page"] == 1
    assert data["page_size"] == 20


def test_superintendent_escalations_officer_403(client: TestClient, officer_roads: tuple) -> None:
    """RBAC-01: Department officer cannot view superintendent escalations."""
    _, token = officer_roads
    res = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_superintendent_escalations_citizen_403(client: TestClient, citizen_user: tuple) -> None:
    """RBAC-01: Citizen cannot view superintendent escalations."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/superintendent/escalations",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_superintendent_escalations_anonymous_401(client: TestClient) -> None:
    """RBAC-01: Anonymous access returns 401."""
    res = client.get("/api/v1/superintendent/escalations")
    assert res.status_code == 401
