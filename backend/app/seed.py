"""Phase 3 seed placeholder.

Phase 4 replaces this with an idempotent seed of departments, categories, and
demo users. Keeping the command wired now means `make seed` is a stable entry
point for developers and CI.
"""
from __future__ import annotations

import logging

from app.core.logging import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info(
        "event=seed_skipped reason=phase_4_not_implemented seed_demo_data=%s",
        False,
    )


if __name__ == "__main__":
    main()
