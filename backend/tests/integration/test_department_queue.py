"""
CivicTrack — Department Queue Integration Tests (FR-017, TRD §8.5)

Tests the department complaint queue endpoint.
"""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_department_queue_officer(client: TestClient, officer_roads: tuple) -> None:
    """FR-017: Department officer can view their department's complaint queue."""
    _, token = officer_roads
    res = client.get(
        "/api/v1/department/complaints",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["department_id"] == officer_roads[0].department_id
    assert data["page"] == 1
    assert data["page_size"] == 20


def test_department_queue_citizen_403(client: TestClient, citizen_user: tuple) -> None:
    """RBAC-01: Citizen cannot view department queue."""
    _, token = citizen_user
    res = client.get(
        "/api/v1/department/complaints",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_department_queue_anonymous_401(client: TestClient) -> None:
    """RBAC-01: Anonymous access returns 401."""
    res = client.get("/api/v1/department/complaints")
    assert res.status_code == 401
