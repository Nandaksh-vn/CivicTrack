"""
CivicTrack — Upload Security Tests (TEST-051, NFR-013, SEC-09, TRD §10)
"""

from __future__ import annotations

import io

from app.core.security import hash_password
from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Role, Status
from app.models.user import User
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy.orm import Session


def _create_sample_image(format_name: str = "PNG", size: tuple[int, int] = (10, 10)) -> bytes:
    """Generate valid image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=(255, 0, 0))
    img.save(buf, format=format_name)
    return buf.getvalue()


def test_magic_byte_bypass_rejected(
    client: TestClient,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    db: Session,
) -> None:
    """TEST-051, NFR-013, SEC-09: Renamed executable/script payload fails magic byte validation."""
    citizen, token = citizen_user
    headers = {"Authorization": f"Bearer {token}"}

    complaint = Complaint(
        complaint_number="CT-2026-000771",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole With Suspicious Upload",
        description="Description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()

    # Fake JPEG: plain text shell script disguised as JPEG
    fake_jpeg = b"#!/bin/bash\necho 'malicious code'\n"
    files = {"file": ("malicious.jpg", fake_jpeg, "image/jpeg")}
    data = {"kind": "PROGRESS"}

    resp = client.post(
        f"/api/v1/complaints/{complaint.id}/images",
        files=files,
        data=data,
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "INVALID_IMAGE_SIGNATURE"


def test_oversize_image_rejected(
    client: TestClient,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    db: Session,
) -> None:
    """TEST-051, NFR-013: Uploads exceeding 5 MiB are rejected with 422."""
    citizen, token = citizen_user
    headers = {"Authorization": f"Bearer {token}"}

    complaint = Complaint(
        complaint_number="CT-2026-000772",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole With Oversize Upload",
        description="Description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()

    # 5.1 MiB payload with valid PNG header
    png_header = b"\x89PNG\r\n\x1a\n"
    oversize_payload = png_header + (b"\x00" * (5 * 1024 * 1024 + 1024))
    files = {"file": ("huge.png", oversize_payload, "image/png")}

    resp = client.post(
        f"/api/v1/complaints/{complaint.id}/images",
        files=files,
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "FILE_TOO_LARGE"


def test_path_traversal_sanitized_and_blocked(
    client: TestClient,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    db: Session,
) -> None:
    """TEST-051, SEC-09: Directory traversal in original filename is stripped."""
    citizen, token = citizen_user
    headers = {"Authorization": f"Bearer {token}"}

    complaint = Complaint(
        complaint_number="CT-2026-000773",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Traversal Test",
        description="Description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()

    png_bytes = _create_sample_image("PNG")
    # Traversal in filename
    files = {"file": ("../../../../etc/passwd.png", png_bytes, "image/png")}

    resp = client.post(
        f"/api/v1/complaints/{complaint.id}/images",
        files=files,
        headers=headers,
    )
    assert resp.status_code == 201
    record = resp.json()
    # Check sanitized filename
    assert ".." not in record["original_filename"]
    assert "/" not in record["original_filename"]
    assert "\\" not in record["original_filename"]


def test_decompression_bomb_dimensions_rejected(
    client: TestClient,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    db: Session,
) -> None:
    """TEST-051: Image dimensions exceeding 10,000 x 10,000 are rejected (decompression bomb protection)."""
    citizen, token = citizen_user
    headers = {"Authorization": f"Bearer {token}"}

    complaint = Complaint(
        complaint_number="CT-2026-000774",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Pothole Bomb Test",
        description="Description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()

    # Image with dimensions 10,001 x 10
    huge_dim_bytes = _create_sample_image("PNG", size=(10001, 10))
    files = {"file": ("bomb.png", huge_dim_bytes, "image/png")}

    resp = client.post(
        f"/api/v1/complaints/{complaint.id}/images",
        files=files,
        headers=headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"] == "IMAGE_TOO_LARGE"


def test_image_streaming_authorization_and_headers(
    client: TestClient,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
    db: Session,
) -> None:
    """TEST-051, TRD §10.3: Images are served under auth, with private cache and inline disposition."""
    citizen_a, token_a = citizen_user
    headers_a = {"Authorization": f"Bearer {token_a}"}

    complaint = Complaint(
        complaint_number="CT-2026-000775",
        citizen_id=citizen_a.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Image Auth Complaint",
        description="Description.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()

    # Upload valid PNG
    png_bytes = _create_sample_image("PNG")
    upload_resp = client.post(
        f"/api/v1/complaints/{complaint.id}/images",
        files={"file": ("evidence.png", png_bytes, "image/png")},
        headers=headers_a,
    )
    assert upload_resp.status_code == 201
    image_id = upload_resp.json()["id"]

    # 1. Citizen A streams own image -> 200 OK
    stream_resp = client.get(
        f"/api/v1/complaints/{complaint.id}/images/{image_id}/file",
        headers=headers_a,
    )
    assert stream_resp.status_code == 200
    assert stream_resp.headers["content-type"] == "image/png"
    assert "private" in stream_resp.headers["cache-control"]
    assert "inline" in stream_resp.headers["content-disposition"]

    # 2. Citizen B attempts to stream Citizen A's image -> 403 Forbidden
    citizen_b = User(
        full_name="Other Citizen",
        email="other@demo.local",
        password_hash=hash_password("Other123"),
        role=Role.CITIZEN,
        is_active=True,
    )
    db.add(citizen_b)
    db.commit()

    from app.core.security import create_access_token

    token_b, _ = create_access_token(citizen_b.id, citizen_b.role.value)
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_stranger = client.get(
        f"/api/v1/complaints/{complaint.id}/images/{image_id}/file",
        headers=headers_b,
    )
    assert resp_stranger.status_code == 403
    assert resp_stranger.json()["error"] == "FORBIDDEN"
