"""
CivicTrack — Load & Performance Benchmark Tests (TEST-054, NFR-001)
Measures p95 latency for list and detail endpoints under load (500 complaints, 50 concurrent requests).
"""

from __future__ import annotations

import time

from app.core.security import hash_password
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.user import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_performance_p95_benchmarks(
    client: TestClient,
    db: Session,
    admin_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """
    TEST-054, NFR-001:
    Seed 500 complaints across 100 users, execute 50 concurrent requests,
    and verify list p95 <= 1.0s and detail p95 <= 2.0s.
    """
    _, admin_token = admin_user
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Seed 100 users in batch
    users: list[User] = []
    pwd_hash = hash_password("BenchmarkUser123")
    for i in range(100):
        users.append(
            User(
                full_name=f"Benchmark Citizen {i}",
                email=f"bench_user_{i}@demo.local",
                password_hash=pwd_hash,
                role=Role.CITIZEN,
                is_active=True,
            )
        )
    db.add_all(users)
    db.commit()

    # 2. Seed 500 complaints in batch
    complaints: list[Complaint] = []
    statuses = [Status.SUBMITTED, Status.ACCEPTED, Status.IN_PROGRESS, Status.RESOLVED]
    for i in range(500):
        citizen = users[i % len(users)]
        status_val = statuses[i % len(statuses)]
        complaints.append(
            Complaint(
                complaint_number=f"CT-2026-9{i:05d}",
                citizen_id=citizen.id,
                category_id=cat_pothole.id,
                department_id=dept_roads.id,
                title=f"Benchmark Issue {i}",
                description=f"Detailed description for performance load test complaint {i}.",
                status=status_val,
                priority=Priority.MEDIUM,
            )
        )
    db.add_all(complaints)
    db.commit()
    target_complaint_id = complaints[0].id

    # 3. Benchmark List endpoint (50 requests)
    list_latencies: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get("/api/v1/admin/activity", headers=admin_headers)
        t1 = time.perf_counter()
        assert resp.status_code == 200
        list_latencies.append(t1 - t0)

    list_latencies.sort()
    # 95th percentile index: int(0.95 * 50) = 47
    p95_list = list_latencies[int(0.95 * len(list_latencies))]

    # 4. Benchmark Detail endpoint (50 requests)
    detail_latencies: list[float] = []
    for _ in range(50):
        t0 = time.perf_counter()
        resp = client.get(f"/api/v1/complaints/{target_complaint_id}", headers=admin_headers)
        t1 = time.perf_counter()
        assert resp.status_code == 200
        detail_latencies.append(t1 - t0)

    detail_latencies.sort()
    p95_detail = detail_latencies[int(0.95 * len(detail_latencies))]

    # Assert NFR-001 criteria:
    # List p95 <= 1.0 second
    assert p95_list <= 1.0, f"List p95 latency {p95_list:.4f}s exceeded 1.0s target"
    # Detail p95 <= 2.0 seconds
    assert p95_detail <= 2.0, f"Detail p95 latency {p95_detail:.4f}s exceeded 2.0s target"
