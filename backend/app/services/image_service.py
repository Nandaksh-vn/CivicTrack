"""
CivicTrack — Image Storage & Security Service (TRD §10, NFR-013, SEC-09, TEST-051, TEST-057)
"""

from __future__ import annotations

import io
import logging
import re
import uuid
from pathlib import Path

from PIL import Image
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utcnow
from app.core.config import settings
from app.core.errors import AppError, BadRequest, Conflict, Forbidden, NotFound, UnprocessableEntity
from app.models.complaint import Complaint
from app.models.enums import ImageKind, Role
from app.models.image import ComplaintImage
from app.models.user import User

logger = logging.getLogger(__name__)

# Constants per TRD §10.4
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MiB
MAX_FILES_PER_REQUEST = 3
MAX_IMAGES_PER_COMPLAINT = 10
MAX_IMAGE_DIMENSION = 10_000
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_PIL_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}

_MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
}


def sanitize_filename(filename: str) -> str:
    """Sanitize original filename for display; prevent directory traversal or control characters."""
    basename = Path(filename).name
    clean = re.sub(r"\.{2,}", "_", basename)
    clean = re.sub(r"[^\w\.\-\s]", "_", clean).strip()
    return clean[:255] or "uploaded_image"


def validate_image_content(content: bytes, content_type: str) -> str:
    """
    Validate size, magic bytes, Pillow integrity, dimensions, and format (NFR-013, SEC-09).
    Returns the normalized extension ('jpg', 'png', 'webp').
    """
    # 1. Size check
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise UnprocessableEntity(
            message=f"File exceeds maximum allowed size of {settings.max_upload_mb} MiB.",
            error_code="FILE_TOO_LARGE",
        )

    # 2. Content-Type check
    if content_type not in ALLOWED_MIME_TYPES:
        raise UnprocessableEntity(
            message=f"MIME type '{content_type}' is not allowed. Allowed types: JPEG, PNG, WebP.",
            error_code="INVALID_MIME_TYPE",
        )

    # 3. Magic-bytes check (protects against renamed executables or non-image payloads)
    valid_magic = False
    for magic in _MAGIC_BYTES.get(content_type, []):
        if content.startswith(magic):
            if content_type == "image/webp":
                # WebP requires 'WEBP' at byte offset 8..12
                if len(content) >= 12 and content[8:12] == b"WEBP":
                    valid_magic = True
            else:
                valid_magic = True
            break

    if not valid_magic:
        raise UnprocessableEntity(
            message="File contents do not match the declared image signature.",
            error_code="INVALID_IMAGE_SIGNATURE",
        )

    # 4. Pillow verification + Decompression bomb check
    try:
        with Image.open(io.BytesIO(content)) as img:
            img.verify()
            detected_format = img.format
    except Exception as exc:
        raise UnprocessableEntity(
            message="Corrupted or invalid image data.",
            error_code="CORRUPT_IMAGE",
        ) from exc

    if detected_format not in ALLOWED_PIL_FORMATS:
        raise UnprocessableEntity(
            message=f"Detected image format '{detected_format}' is not permitted.",
            error_code="INVALID_IMAGE_FORMAT",
        )

    # Re-open for dimensions check after verify()
    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size
            if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise UnprocessableEntity(
                    message=f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION}.",
                    error_code="IMAGE_TOO_LARGE",
                )
    except AppError:
        raise
    except Exception as exc:
        raise UnprocessableEntity(
            message="Failed to inspect image dimensions.",
            error_code="CORRUPT_IMAGE",
        ) from exc

    return ALLOWED_PIL_FORMATS[detected_format]


def store_complaint_image(
    db: Session,
    complaint_id: int,
    user: User,
    content: bytes,
    filename: str,
    content_type: str,
    kind: ImageKind = ImageKind.SUBMISSION,
    base_upload_dir: str | None = None,
) -> ComplaintImage:
    """
    Validate, store file on disk, and record database metadata atomically (TRD §10).
    """
    upload_root = Path(base_upload_dir or settings.upload_dir).resolve()

    # Verify complaint exists
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise NotFound(message="Complaint not found.", error_code="NOT_FOUND")

    # Check total image limit per complaint (max 10)
    current_image_count = (
        db.scalar(
            select(func.count(ComplaintImage.id)).where(ComplaintImage.complaint_id == complaint_id)
        )
        or 0
    )
    if current_image_count >= MAX_IMAGES_PER_COMPLAINT:
        raise Conflict(
            message=f"Complaint already has the maximum of {MAX_IMAGES_PER_COMPLAINT} images.",
            error_code="IMAGE_LIMIT_EXCEEDED",
        )

    # Validate image data & retrieve extension
    ext = validate_image_content(content, content_type)
    safe_name = sanitize_filename(filename)

    now = utcnow()
    year = f"{now.year:04d}"
    month = f"{now.month:02d}"

    # Target folder: {upload_dir}/{year}/{month}/{complaint_id}/
    target_dir = (upload_root / year / month / str(complaint_id)).resolve()

    # Prevent directory traversal
    if not str(target_dir).startswith(str(upload_root)):
        raise BadRequest(
            message="Invalid storage path.",
            error_code="PATH_TRAVERSAL_DETECTED",
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    # Random unique file name
    file_id = uuid.uuid4().hex
    final_filename = f"{file_id}.{ext}"
    final_path = target_dir / final_filename
    temp_path = target_dir / f"{file_id}.tmp"

    try:
        # Atomic write
        temp_path.write_bytes(content)
        temp_path.replace(final_path)

        relative_path = str(final_path.relative_to(upload_root)).replace("\\", "/")

        image_record = ComplaintImage(
            complaint_id=complaint.id,
            uploaded_by_user_id=user.id,
            kind=kind,
            storage_path=relative_path,
            original_filename=safe_name,
            mime_type=content_type,
            size_bytes=len(content),
            created_at=now,
        )
        db.add(image_record)
        db.commit()
        db.refresh(image_record)
        return image_record
    except Exception as exc:
        db.rollback()
        # Clean up temporary or stored file on failure
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        if final_path.exists():
            final_path.unlink(missing_ok=True)
        logger.error("Failed to store image: %s", exc)
        raise


def resolve_image_file_path(
    db: Session,
    complaint_id: int,
    image_id: int,
    user: User,
    base_upload_dir: str | None = None,
) -> tuple[Path, ComplaintImage]:
    """
    Verify role & object permissions, resolve file path safely, and check traversal (TRD §10.3).
    """
    upload_root = Path(base_upload_dir or settings.upload_dir).resolve()

    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise NotFound(message="Complaint not found.", error_code="NOT_FOUND")

    # Object-scope checks
    if user.role == Role.CITIZEN and complaint.citizen_id != user.id:
        raise Forbidden(
            message="You do not have permission to view images of this complaint.",
            error_code="FORBIDDEN",
        )
    if user.role == Role.DEPARTMENT_OFFICER:
        if user.department_id != complaint.department_id:
            raise Forbidden(
                message="You do not have permission to view images of another department's complaint.",
                error_code="FORBIDDEN",
            )

    image = db.execute(
        select(ComplaintImage).where(
            ComplaintImage.id == image_id,
            ComplaintImage.complaint_id == complaint_id,
        )
    ).scalar_one_or_none()

    if not image:
        raise NotFound(message="Image not found.", error_code="NOT_FOUND")

    file_path = (upload_root / image.storage_path).resolve()

    # Path traversal guard
    if not str(file_path).startswith(str(upload_root)):
        raise Forbidden(
            message="Access to path outside upload root is forbidden.",
            error_code="PATH_TRAVERSAL_DETECTED",
        )

    if not file_path.exists():
        raise NotFound(message="Image file missing from storage.", error_code="FILE_NOT_FOUND")

    return file_path, image
