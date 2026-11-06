"""
CivicTrack — Log Privacy & PII Audit Tests (TEST-052, NFR-021, SEC-11)
"""

from __future__ import annotations

import io
import logging

from app.core.logging import SensitiveDataFilter


def test_log_sanitizer_redacts_tokens() -> None:
    """TEST-052, NFR-021: Bearer tokens in logs are redacted."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Request received with auth header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.dummy.sig",
        args=(),
        exc_info=None,
    )
    s_filter = SensitiveDataFilter()
    assert s_filter.filter(record)
    assert "Bearer [REDACTED_TOKEN]" in record.msg
    assert "eyJhbGci" not in record.msg


def test_log_sanitizer_redacts_passwords_and_secrets() -> None:
    """TEST-052, NFR-021: Passwords and secrets in log messages are redacted."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Authentication failed for user payload: password='MySecretPassword123' token=secret_token_abc",
        args=(),
        exc_info=None,
    )
    s_filter = SensitiveDataFilter()
    assert s_filter.filter(record)
    assert "MySecretPassword123" not in record.msg
    assert "secret_token_abc" not in record.msg
    assert "password=[REDACTED]" in record.msg


def test_log_sanitizer_redacts_emails_and_phones() -> None:
    """TEST-052, NFR-021: Citizen emails and phone numbers in logs are redacted."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="User registered: email=priya.patel@example.com phone=+91 98765 43210 successfully.",
        args=(),
        exc_info=None,
    )
    s_filter = SensitiveDataFilter()
    assert s_filter.filter(record)
    assert "priya.patel@example.com" not in record.msg
    assert "+91 98765 43210" not in record.msg
    assert "[REDACTED_EMAIL]" in record.msg
    assert "[REDACTED_PHONE]" in record.msg


def test_log_sanitizer_redacts_coordinates() -> None:
    """TEST-052, NFR-021: Precise geographic coordinates in logs are redacted."""
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="Complaint pinned at coordinates: 12.971598, 77.594562 on map.",
        args=(),
        exc_info=None,
    )
    s_filter = SensitiveDataFilter()
    assert s_filter.filter(record)
    assert "12.971598, 77.594562" not in record.msg
    assert "[REDACTED_COORDINATES]" in record.msg


def test_log_stream_capture_has_no_pii() -> None:
    """TEST-052: Real stream handler with filter applied intercepts sensitive information."""
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(SensitiveDataFilter())

    logger = logging.getLogger("test_capture_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    try:
        logger.info(
            "Sensitive event: token=secret-token user=citizen@civic.test latlon=28.613939, 77.209021"
        )
        output = stream.getvalue()
        assert "secret-token" not in output
        assert "citizen@civic.test" not in output
        assert "28.613939, 77.209021" not in output
    finally:
        logger.removeHandler(handler)
