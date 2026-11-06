"""
CivicTrack - APScheduler escalation worker entrypoint (TRD sections 1.3 and 11).

Runs as a separate container and shares the Python package with the API. The
real escalation service is added in Phase 11; Phase 3 only wires the scheduler
and validates the worker process stays alive.
"""

from __future__ import annotations

import logging
import sys

from apscheduler.schedulers.blocking import BlockingScheduler

from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def run_escalation_check() -> None:
    """Placeholder for the Phase 11 escalation service call."""
    logger.info(
        "event=escalation_run status=stub window_minutes=%s demo_mode=%s",
        settings.escalation_window_minutes,
        settings.demo_mode,
    )


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
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("event=worker_stop")
        sys.exit(0)


if __name__ == "__main__":
    main()
