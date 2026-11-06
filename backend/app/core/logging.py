"""
CivicTrack — Structured logging configuration (TRD §5.8, NFR-021)
JSON / formatted output to stdout; collected by Docker log driver.
No PII, tokens, emails, phone numbers, or coordinates in log messages.
"""

from __future__ import annotations

import logging
import re
import sys

from app.core.config import settings

# Patterns for sensitive data redaction (NFR-021)
_REDACTION_PATTERNS = [
    # Bearer tokens
    (re.compile(r"Bearer\s+[A-Za-z0-9\-_\.]+", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    # Password / secret assignments
    (
        re.compile(r"(?i)(password|secret|token|api_key|auth_token)\s*[:=]\s*['\"]?[^\s,'\"]+"),
        r"\1=[REDACTED]",
    ),
    # Email addresses
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # Phone numbers (7 to 15 digits with optional country code and common separators)
    (
        re.compile(r"(?:\+?\d{1,3}[\s-]*)?(?:\d[\s-]*){7,14}\d"),
        "[REDACTED_PHONE]",
    ),
    # High-precision coordinates (lat, lon)
    (
        re.compile(r"\b-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b"),
        "[REDACTED_COORDINATES]",
    ),
]


class SensitiveDataFilter(logging.Filter):
    """Filter that sanitizes log messages to guarantee NFR-021 compliance."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern, replacement in _REDACTION_PATTERNS:
                sanitized = pattern.sub(replacement, sanitized)
            record.msg = sanitized

        if record.args:
            # If formatted arguments contain strings, scrub them too
            if isinstance(record.args, dict):
                record.args = {
                    k: self._scrub_string(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._scrub_string(v) if isinstance(v, str) else v for v in record.args
                )
        return True

    @staticmethod
    def _scrub_string(val: str) -> str:
        for pattern, replacement in _REDACTION_PATTERNS:
            val = pattern.sub(replacement, val)
        return val


def configure_logging() -> None:
    """Configure root logger with level from settings and attach SensitiveDataFilter."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(formatter)
    handler.addFilter(SensitiveDataFilter())

    # Replace existing handlers
    root_logger.handlers = [handler]

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
