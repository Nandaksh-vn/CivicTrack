"""
CivicTrack — Clock abstraction (TRD §5.7)
All application code must obtain the current time through this module so that
tests can monkeypatch `utcnow` without touching the standard library.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utcnow() -> datetime:
    """
    Return the current UTC time as a timezone-naive datetime with microsecond
    precision, suitable for storage in MySQL DATETIME(6) columns.

    MySQL stores naive UTC; the API serializes with a 'Z' suffix.
    Application code MUST NOT call datetime.now() or datetime.utcnow() directly.
    """
    return datetime.now(UTC).replace(tzinfo=None)
