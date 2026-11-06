"""
CivicTrack — Enum Unit Tests

Tests canonical enumeration values for Role, Status, Priority, and related
enums (TRD §3.1, §3.2, §7).
"""

from __future__ import annotations

from app.models.enums import (
    CommentType,
    CommentVisibility,
    ImageKind,
    OfficerActionType,
    Priority,
    Role,
    Status,
    TriggerSource,
)

# ── Role ─────────────────────────────────────────────────────────────────────


def test_role_values() -> None:
    assert Role.CITIZEN == "CITIZEN"
    assert Role.DEPARTMENT_OFFICER == "DEPARTMENT_OFFICER"
    assert Role.SUPERINTENDENT_OFFICER == "SUPERINTENDENT_OFFICER"
    assert Role.PLATFORM_ADMIN == "PLATFORM_ADMIN"


def test_role_members() -> None:
    assert set(Role) == {
        Role.CITIZEN,
        Role.DEPARTMENT_OFFICER,
        Role.SUPERINTENDENT_OFFICER,
        Role.PLATFORM_ADMIN,
    }


# ── Status ───────────────────────────────────────────────────────────────────


def test_status_values() -> None:
    assert Status.SUBMITTED == "SUBMITTED"
    assert Status.PENDING_DEPARTMENT_REVIEW == "PENDING_DEPARTMENT_REVIEW"
    assert Status.ACCEPTED == "ACCEPTED"
    assert Status.IN_PROGRESS == "IN_PROGRESS"
    assert Status.REJECTED == "REJECTED"
    assert Status.ESCALATED == "ESCALATED"
    assert Status.RESOLVED == "RESOLVED"
    assert Status.REOPENED == "REOPENED"


def test_status_members() -> None:
    assert len(list(Status)) == 8


# ── Priority ─────────────────────────────────────────────────────────────────


def test_priority_values() -> None:
    assert Priority.LOW == "LOW"
    assert Priority.MEDIUM == "MEDIUM"
    assert Priority.HIGH == "HIGH"


# ── ImageKind ────────────────────────────────────────────────────────────────


def test_image_kind_values() -> None:
    assert ImageKind.SUBMISSION == "SUBMISSION"
    assert ImageKind.PROGRESS == "PROGRESS"
    assert ImageKind.RESOLUTION == "RESOLUTION"
    assert ImageKind.REOPEN == "REOPEN"


# ── CommentType / CommentVisibility ──────────────────────────────────────────


def test_comment_type_values() -> None:
    assert CommentType.PROGRESS_NOTE == "PROGRESS_NOTE"
    assert CommentType.CITIZEN_FEEDBACK == "CITIZEN_FEEDBACK"


def test_comment_visibility_values() -> None:
    assert CommentVisibility.CITIZEN_VISIBLE == "CITIZEN_VISIBLE"
    assert CommentVisibility.INTERNAL == "INTERNAL"


# ── OfficerActionType ────────────────────────────────────────────────────────


def test_officer_action_type_values() -> None:
    assert OfficerActionType.INSTRUCTION == "INSTRUCTION"
    assert OfficerActionType.FOLLOW_UP == "FOLLOW_UP"
    assert OfficerActionType.REASSIGN == "REASSIGN"
    assert OfficerActionType.NOTE == "NOTE"


# ── TriggerSource ────────────────────────────────────────────────────────────


def test_trigger_source_values() -> None:
    assert TriggerSource.SCHEDULER == "SCHEDULER"
    assert TriggerSource.MANUAL_TRIGGER == "MANUAL_TRIGGER"
    assert TriggerSource.DEMO_SEED == "DEMO_SEED"
