"""Prometheus metrics endpoint."""

from __future__ import annotations

import secrets
from typing import Annotated

from fastapi import APIRouter, Header, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.config import settings
from app.core.exceptions import AppError

router = APIRouter(tags=["metrics"])


def _authorize_metrics(authorization: str | None) -> None:
    """
    Dev: open scrape for local Prometheus.

    Staging/production: require Authorization: Bearer <METRICS_TOKEN>.
    Missing token config → 503 so misconfigured deploys fail loudly.
    """
    if settings.ENVIRONMENT == "dev":
        return

    expected = settings.METRICS_TOKEN
    if not expected:
        raise AppError(
            detail="Metrics endpoint is not configured (set METRICS_TOKEN)",
            status_code=503,
        )

    if authorization is None or not authorization.startswith("Bearer "):
        raise AppError(
            detail="Missing or invalid Authorization bearer token",
            status_code=401,
        )

    provided = authorization.removeprefix("Bearer ").strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise AppError(
            detail="Missing or invalid Authorization bearer token",
            status_code=401,
        )


@router.get("/metrics", include_in_schema=False)
async def metrics(
    authorization: Annotated[str | None, Header()] = None,
) -> Response:
    """Expose Prometheus metrics (token-gated outside dev)."""
    _authorize_metrics(authorization)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
