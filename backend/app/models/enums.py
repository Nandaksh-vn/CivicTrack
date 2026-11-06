"""
CivicTrack — Canonical Enums (TRD §3.1, §3.2, §7)
"""

from __future__ import annotations

import enum


class Role(enum.StrEnum):
    CITIZEN = "CITIZEN"
    DEPARTMENT_OFFICER = "DEPARTMENT_OFFICER"
    SUPERINTENDENT_OFFICER = "SUPERINTENDENT_OFFICER"
    PLATFORM_ADMIN = "PLATFORM_ADMIN"


class Status(enum.StrEnum):
    SUBMITTED = "SUBMITTED"
    PENDING_DEPARTMENT_REVIEW = "PENDING_DEPARTMENT_REVIEW"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    REOPENED = "REOPENED"


class Priority(enum.StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ImageKind(enum.StrEnum):
    SUBMISSION = "SUBMISSION"
    PROGRESS = "PROGRESS"
    RESOLUTION = "RESOLUTION"
    REOPEN = "REOPEN"


class CommentType(enum.StrEnum):
    PROGRESS_NOTE = "PROGRESS_NOTE"
    CITIZEN_FEEDBACK = "CITIZEN_FEEDBACK"


class CommentVisibility(enum.StrEnum):
    CITIZEN_VISIBLE = "CITIZEN_VISIBLE"
    INTERNAL = "INTERNAL"


class OfficerActionType(enum.StrEnum):
    INSTRUCTION = "INSTRUCTION"
    FOLLOW_UP = "FOLLOW_UP"
    REASSIGN = "REASSIGN"
    NOTE = "NOTE"


class TriggerSource(enum.StrEnum):
    SCHEDULER = "SCHEDULER"
    MANUAL_TRIGGER = "MANUAL_TRIGGER"
    DEMO_SEED = "DEMO_SEED"
