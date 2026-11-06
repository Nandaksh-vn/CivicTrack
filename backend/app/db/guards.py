"""Append-only enforcement for history/escalation/action/audit tables.

The application boundary is authoritative: a SQLAlchemy `before_flush`
listener raises before any UPDATE or DELETE can reach the database.
Optional MySQL trigger DDL is documented in `docs/DATA_MODEL.md`; the
oracle is deliberately the application layer so the test harness exercises
the same guard.
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.complaint_status_history import ComplaintStatusHistory
from app.models.escalation import Escalation
from app.models.officer_action import OfficerAction


class AppendOnlyViolation(RuntimeError):
    """Raised when code attempts to mutate an append-only row."""


APPEND_ONLY_MODELS = (ComplaintStatusHistory, Escalation, OfficerAction, AuditLog)


def _find_append_only_changes(session: Session) -> list[str]:
    changes: list[str] = []
    for model in APPEND_ONLY_MODELS:
        for obj in session.dirty:
            if isinstance(obj, model) and session.is_modified(obj, include_collections=False):
                changes.append(f"UPDATE {model.__tablename__}")
        for obj in session.deleted:
            if isinstance(obj, model):
                changes.append(f"DELETE {model.__tablename__}")
    return changes


@event.listens_for(Session, "before_flush", insert=True)
def _enforce_append_only(session: Session, _context: object, _targets: object) -> None:
    changes = _find_append_only_changes(session)
    if changes:
        raise AppendOnlyViolation(
            "Append-only tables rejected a mutation: " + "; ".join(sorted(set(changes)))
        )
