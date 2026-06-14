"""
Delete expired OTP codes older than OTP_RETENTION_DAYS.

Production: use scripts/pg_cron_otp_cleanup.sql (pg_cron daily job).
Local/staging: run manually or via cron:

    uv run python -m scripts.cleanup_otp_codes
"""

from __future__ import annotations

import asyncio
from datetime import timedelta

import structlog

from app.core.config import settings
from app.core.datetime_utils import utc_now
from app.core.uow import uow_scope

logger = structlog.get_logger(__name__)


async def cleanup_otp_codes() -> int:
    """Remove otp_codes expired longer than OTP_RETENTION_DAYS ago."""
    cutoff = utc_now() - timedelta(days=settings.OTP_RETENTION_DAYS)
    async with uow_scope() as uow:
        deleted = await uow.otp_codes.delete_expired_before(cutoff)
    logger.info(
        "otp_codes_cleanup_complete",
        deleted=deleted,
        retention_days=settings.OTP_RETENTION_DAYS,
        cutoff=cutoff.isoformat(),
    )
    return deleted


def main() -> None:
    deleted = asyncio.run(cleanup_otp_codes())
    print(f"Deleted {deleted} expired OTP code row(s).")


if __name__ == "__main__":
    main()
