"""Startup checks that fail fast on unsafe production configuration."""

from __future__ import annotations

import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


def api_docs_route_kwargs(environment: str) -> dict[str, str | None]:
    """
    OpenAPI UI routes for FastAPI constructor kwargs.

    WHY: /docs and /openapi.json are reconnaissance surfaces — only expose in dev.
    """
    if environment == "dev":
        return {
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
        }
    return {"docs_url": None, "redoc_url": None, "openapi_url": None}


def validate_production_rate_limit_config() -> None:
    """
    Require Redis-backed rate limits in production unless explicitly overridden.

    WHY: SlowAPI in-memory counters are per-process. Multiple replicas without
    REDIS_URL silently weaken OTP/refresh limits.
    """
    if not settings.is_production:
        return
    if settings.REDIS_URL:
        return
    if settings.ALLOW_INMEMORY_RATE_LIMIT:
        logger.warning(
            "production_inmemory_rate_limit_allowed",
            detail="ALLOW_INMEMORY_RATE_LIMIT=true; unsafe with multiple API instances",
        )
        return
    raise RuntimeError(
        "REDIS_URL is required when ENVIRONMENT=production. "
        "Set REDIS_URL for distributed rate limiting, or set "
        "ALLOW_INMEMORY_RATE_LIMIT=true only for a single-instance emergency."
    )
