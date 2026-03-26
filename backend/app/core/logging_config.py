"""
Logging configuration.

Uses `structlog` to produce structured logs:
- JSON in production
- readable console output in development

Also enforces required fields:
- `timestamp`
- `level`
- `service`
- `request_id` (defaults to `unknown` when not provided)
"""

from __future__ import annotations

import logging

import structlog

from app.core.config import settings


def _add_service(
    _: object,
    __: str,
    event_dict: dict,
) -> dict:
    event_dict.setdefault("service", settings.APP_NAME)
    return event_dict


def _ensure_request_id(
    _: object,
    __: str,
    event_dict: dict,
) -> dict:
    if not event_dict.get("request_id"):
        event_dict["request_id"] = "unknown"
    return event_dict


def setup_logging() -> None:
    """Configure stdlib + structlog for the whole app."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    structlog.stdlib.recreate_defaults(level=level)

    if settings.DEBUG:
        renderer = structlog.dev.ConsoleRenderer(colors=False)
    else:
        renderer = structlog.processors.JSONRenderer()

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.add_log_level,
            _add_service,
            _ensure_request_id,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )

    # Reduce noise from uvicorn access logs.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
