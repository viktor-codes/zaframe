"""
Run booking lifecycle every 5 minutes — for platforms without a native cron job.

Prefer the one-shot script via Render/Railway cron when available:

    python -m scripts.run_booking_lifecycle

Use this loop only as a long-running worker process (see Procfile `worker`).
"""

from __future__ import annotations

import asyncio
import os

import structlog

from scripts.run_booking_lifecycle import run_booking_lifecycle

logger = structlog.get_logger(__name__)

DEFAULT_INTERVAL_SECONDS = 300


def _interval_seconds() -> int:
    raw = os.environ.get("BOOKING_LIFECYCLE_INTERVAL_SECONDS", str(DEFAULT_INTERVAL_SECONDS))
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS
    return value if value >= 30 else DEFAULT_INTERVAL_SECONDS


async def loop_forever() -> None:
    """Invoke lifecycle repeatedly until the process is stopped."""
    interval = _interval_seconds()
    logger.info("booking_lifecycle_loop_started", interval_seconds=interval)
    while True:
        try:
            await run_booking_lifecycle()
        except Exception:
            # WHY: keep the worker alive across transient DB blips; alert via logs.
            logger.exception("booking_lifecycle_loop_iteration_failed")
        await asyncio.sleep(interval)


def main() -> None:
    asyncio.run(loop_forever())


if __name__ == "__main__":
    main()
