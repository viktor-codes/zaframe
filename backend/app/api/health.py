"""Health endpoints.

`/health` is a lightweight health check (DB connectivity is required by rules).
`/health/ready` is a readiness check (DB + optional Stripe/Resend).
"""

from typing import Any

import structlog
from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.database import engine

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to ZeeFrame API - Irish Dance & Yoga Booking"}


@router.get("/health")
async def health_check(response: Response) -> dict[str, str]:
    """Validate DB connectivity and return required health payload."""
    db_ok = await _check_database()
    if not db_ok:
        response.status_code = 503
        return {"status": "unready", "version": settings.APP_VERSION, "db": "fail"}
    return {"status": "ok", "version": settings.APP_VERSION, "db": "ok"}


async def _check_database() -> bool:
    """Check DB connectivity (SELECT 1)."""
    logger = structlog.get_logger(__name__)
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning("readiness_db_check_failed", error_type=type(e).__name__)
        return False


async def _check_stripe() -> bool:
    """Check Stripe availability via a lightweight request off the event loop."""
    logger = structlog.get_logger(__name__)
    if not settings.STRIPE_SECRET_KEY:
        return True  # not configured, skip the check
    try:
        from app.modules.payment.stripe_client import get_stripe_client, run_stripe

        client = get_stripe_client()
        await run_stripe(lambda: client.v1.balance.retrieve())
        return True
    except Exception as e:
        logger.warning("readiness_stripe_check_failed", error_type=type(e).__name__)
        return False


def _check_resend_configured() -> bool:
    """Resend: check whether the API key is present."""
    return bool(settings.RESEND_API_KEY)


@router.get("/health/ready")
async def readiness(response: Response) -> dict[str, Any]:
    """
    Readiness: whether the service is ready to accept traffic.

    Checks:
    - DB: required; return 503 when it fails.
    - Stripe: when `STRIPE_SECRET_KEY` is set, do one lightweight request.
    - Resend: only validate whether the API key is configured.
    """
    checks: dict[str, str] = {}

    db_ok = await _check_database()
    checks["database"] = "ok" if db_ok else "fail"
    if not db_ok:
        response.status_code = 503
        return {"status": "unready", "checks": checks}

    if settings.STRIPE_SECRET_KEY:
        stripe_ok = await _check_stripe()
        checks["stripe"] = "ok" if stripe_ok else "fail"
    else:
        checks["stripe"] = "skip"

    if settings.RESEND_API_KEY:
        checks["resend"] = "configured" if _check_resend_configured() else "fail"
    else:
        checks["resend"] = "skip"

    # Return 503 only when DB is unavailable; Stripe/Resend are included for monitoring.
    return {
        "status": "ready",
        "checks": checks,
    }
