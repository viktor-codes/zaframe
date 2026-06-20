"""
Expire stale pending bookings/orders and complete past confirmed bookings.

Production: Render cron job `zaframe-booking-lifecycle` in root render.yaml (every 5 min UTC).
Manual / other hosts:

    */5 * * * * cd /app/backend && python -m scripts.run_booking_lifecycle

Local/staging:

    uv run python -m scripts.run_booking_lifecycle
"""

from __future__ import annotations

import asyncio

import structlog

from app.core.uow_factory import uow_scope
from app.modules.booking import complete_past_confirmed, expire_stale_pending

logger = structlog.get_logger(__name__)


async def run_booking_lifecycle() -> tuple[int, int]:
    """Run pending expiry and confirmed completion in one transaction."""
    async with uow_scope() as uow:
        expired_count = await expire_stale_pending(uow)
        completed_count = await complete_past_confirmed(uow)
    logger.info(
        "booking_lifecycle_complete",
        expired_count=expired_count,
        completed_count=completed_count,
    )
    return expired_count, completed_count


def main() -> None:
    expired_count, completed_count = asyncio.run(run_booking_lifecycle())
    print(
        f"Expired {expired_count} stale pending booking(s); "
        f"completed {completed_count} past confirmed booking(s)."
    )


if __name__ == "__main__":
    main()
