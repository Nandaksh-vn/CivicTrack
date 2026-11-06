"""
CivicTrack — Audit Service (FR-049, FR-050, NFR-008, NFR-019, NFR-021)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.schemas.admin import AuditLogOut

logger = logging.getLogger(__name__)

# Sensitive keys that must be redacted from audit metadata (NFR-021)
_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "authorization",
    "pin",
    "api_key",
}


def _sanitize_metadata(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data:
        return None

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        if any(s in key.lower() for s in _SENSITIVE_KEYS):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = _sanitize_metadata(value)
        elif isinstance(value, datetime):
            sanitized[key] = value.isoformat()
        else:
            sanitized[key] = value
    return sanitized


def record_audit_event(
    db: Session,
    actor_user_id: int | None,
    actor_role: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    commit: bool = True,
) -> AuditLog:
    """
    Append an audit log event (FR-049, FR-050).
    Ensures safe metadata without PII or credential leakage (NFR-021).
    """
    sanitized = _sanitize_metadata(metadata)
    metadata_json = json.dumps(sanitized) if sanitized is not None else None

    audit = AuditLog(
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata_json=metadata_json,
    )

    db.add(audit)
    if commit:
        try:
            db.commit()
            db.refresh(audit)
        except Exception as exc:
            db.rollback()
            logger.error("Failed to commit audit log entry: %s", exc)
            raise
    else:
        db.flush()

    return audit


def list_audit_logs(
    db: Session,
    actor_user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    from_date: datetime | None = None,
    to_date: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditLogOut], int]:
    """
    Query audit log entries with filters and pagination (FR-049).
    Read-only projection, ordered newest first.
    """
    stmt = select(AuditLog)

    if actor_user_id is not None:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if from_date:
        stmt = stmt.where(AuditLog.created_at >= from_date)
    if to_date:
        stmt = stmt.where(AuditLog.created_at <= to_date)

    # Count matching records
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.scalar(count_stmt) or 0

    # Retrieve paginated items
    offset_val = (page - 1) * page_size
    query = (
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .offset(offset_val)
        .limit(page_size)
    )
    records = db.scalars(query).all()

    items: list[AuditLogOut] = []
    for r in records:
        meta: dict[str, Any] | None = None
        if r.metadata_json:
            try:
                meta = json.loads(r.metadata_json)
            except Exception:
                meta = {"raw": r.metadata_json}

        items.append(
            AuditLogOut(
                id=r.id,
                actor_user_id=r.actor_user_id,
                actor_role=r.actor_role,
                action=r.action,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                ip_address=r.ip_address,
                user_agent=r.user_agent,
                metadata=meta,
                created_at=r.created_at,
            )
        )

    return items, total
