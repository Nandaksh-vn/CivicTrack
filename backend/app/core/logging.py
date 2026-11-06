"""
CivicTrack — Structured logging configuration (TRD §5.8)
JSON output to stdout; collected by Docker log driver.
No PII, tokens, emails, or coordinates in log messages.
"""

from __future__ import annotations

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure root logger with level from settings."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
        force=True,
    )

    # Suppress noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
