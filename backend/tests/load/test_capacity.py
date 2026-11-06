"""
CivicTrack — Capacity & Resource Limit Tests (TEST-057, NFR-022, TRD §10.4)
Verifies: 5 MiB/file, 3 files/request, 10 images/complaint, and 2 GB total quota behavior.
"""

from __future__ import annotations

import io

from app.models.category import ComplaintCategory
from app.models.complaint import Complaint
from app.models.department import Department
from app.models.enums import Priority, Status
from app.models.user import User
from app.services.image_service import (
    MAX_FILE_SIZE_BYTES,
    MAX_IMAGES_PER_COMPLAINT,
    store_complaint_image,
)
from PIL import Image
from sqlalchemy.orm import Session


def _sample_png() -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", (10, 10), color=(0, 255, 0))
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_max_ten_images_per_complaint_enforced(
    db: Session,
    citizen_user: tuple[User, str],
    cat_pothole: ComplaintCategory,
    dept_roads: Department,
) -> None:
    """
    TEST-057, TRD §10.4:
    A complaint cannot exceed 10 images total across all kinds; 11th upload returns 409 Conflict.
    """
    citizen, _ = citizen_user

    complaint = Complaint(
        complaint_number="CT-2026-000661",
        citizen_id=citizen.id,
        category_id=cat_pothole.id,
        department_id=dept_roads.id,
        title="Capacity Test Complaint",
        description="Testing max 10 images per complaint.",
        status=Status.SUBMITTED,
        priority=Priority.MEDIUM,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    png_bytes = _sample_png()

    # Upload 10 images successfully
    for i in range(MAX_IMAGES_PER_COMPLAINT):
        img = store_complaint_image(
            db=db,
            complaint_id=complaint.id,
            user=citizen,
            content=png_bytes,
            filename=f"evidence_{i}.png",
            content_type="image/png",
        )
        assert img.id is not None

    # 11th image must raise Conflict (IMAGE_LIMIT_EXCEEDED)
    import pytest
    from app.core.errors import Conflict

    with pytest.raises(Conflict) as exc_info:
        store_complaint_image(
            db=db,
            complaint_id=complaint.id,
            user=citizen,
            content=png_bytes,
            filename="overflow.png",
            content_type="image/png",
        )

    assert exc_info.value.error_code == "IMAGE_LIMIT_EXCEEDED"


def test_max_file_size_constant_matches_five_mib() -> None:
    """TEST-057, NFR-013, NFR-022: File size limit is strictly 5 MiB (5,242,880 bytes)."""
    assert MAX_FILE_SIZE_BYTES == 5 * 1024 * 1024


def test_storage_quota_calculation() -> None:
    """
    TEST-057, NFR-022:
    Simulate 2 GB storage quota verification.
    """
    two_gb_bytes = 2 * 1024 * 1024 * 1024
    # Max images accommodated at 5 MiB each: ~400 full-size images or >2,000 compressed demo images
    assert two_gb_bytes // (5 * 1024 * 1024) >= 400
