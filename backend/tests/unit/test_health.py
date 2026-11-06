from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "1.0.0"}


def test_health_sets_request_id_header() -> None:
    response = client.get("/health", headers={"X-Request-ID": "test-request-id"})

    assert response.headers["X-Request-ID"] == "test-request-id"
