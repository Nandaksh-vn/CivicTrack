"""
CivicTrack - APScheduler escalation worker entrypoint (TRD sections 1.3 and 11).

Runs as a separate container and shares the Python package with the API.
Each tick opens its own database session and runs the idempotent escalation
service so restarts and missed ticks are caught up automatically.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.clock import utcnow
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.models.enums import TriggerSource
from app.services.escalation_service import process_escalations

configure_logging()
logger = logging.getLogger(__name__)


def run_escalation_check() -> None:
    """Run one escalation scan in its own transaction (FR-028, BE-074)."""
    started_at = utcnow()
    db = SessionLocal()
    try:
        escalated = process_escalations(db, trigger_source=TriggerSource.SCHEDULER)
        duration_ms = int((utcnow() - started_at).total_seconds() * 1000)
        logger.info(
            "event=escalation_run status=ok escalated=%s duration_ms=%s window_minutes=%s",
            escalated,
            duration_ms,
            settings.escalation_window_minutes,
        )
    except Exception:
        db.rollback()
        duration_ms = int((utcnow() - started_at).total_seconds() * 1000)
        logger.exception(
            "event=escalation_run status=error duration_ms=%s window_minutes=%s",
            duration_ms,
            settings.escalation_window_minutes,
        )
    finally:
        db.close()


def _next_run(scheduler: BlockingScheduler) -> datetime | None:
    job = scheduler.get_job("escalation_check")
    return job.next_run_time if job else None


def main() -> None:
    logger.info(
        "event=worker_start interval_seconds=%s demo_mode=%s window_minutes=%s",
        settings.escalation_check_seconds,
        settings.demo_mode,
        settings.escalation_window_minutes,
    )

    if settings.demo_mode:
        logger.warning(
            "DEMO MODE: escalation window is %s minutes, not the production default.",
            settings.escalation_window_minutes,
        )

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        run_escalation_check,
        trigger="interval",
        seconds=settings.escalation_check_seconds,
        id="escalation_check",
        max_instances=1,
        coalesce=True,
    )

    try:
        run_escalation_check()
        logger.info("event=worker_next_run next_run_at=%s", _next_run(scheduler))
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("event=worker_stop")
        sys.exit(0)


if __name__ == "__main__":
    main()
