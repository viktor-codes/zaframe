"""Structured logging helpers that keep domain events free of secrets."""

from __future__ import annotations

from typing import Literal, Protocol

from prometheus_client import Counter

SENSITIVE_KEY_PARTS = frozenset(
    {
        "access_token",
        "refresh_token",
        "guest_access_token",
        "raw_guest_access_token",
        "jwt",
        "password",
        "otp",
        "secret",
        "stripe_secret",
        "webhook_secret",
        "client_secret",
        "authorization",
        "cookie",
        "email",
        "phone",
        "customer_name",
        "guest_name",
    }
)

DOMAIN_EVENT_COUNTER = Counter(
    "zaframe_domain_events_total",
    "Domain events logged by application services.",
    ("event", "level"),
)


class StructuredLogger(Protocol):
    """Small protocol for structlog bound loggers used by domain services."""

    def info(self, event: str, **kw: object) -> object: ...

    def warning(self, event: str, **kw: object) -> object: ...

    def error(self, event: str, **kw: object) -> object: ...


def _is_sensitive_key(key: str) -> bool:
    normalized = key.lower()
    return any(part in normalized for part in SENSITIVE_KEY_PARTS)


def safe_log_fields(fields: dict[str, object]) -> dict[str, object]:
    """Drop empty and sensitive fields before they reach the logger."""
    return {
        key: value
        for key, value in fields.items()
        if value is not None and not _is_sensitive_key(key)
    }


def log_domain_event(
    logger: StructuredLogger,
    event: str,
    *,
    level: Literal["info", "warning", "error"] = "info",
    **fields: object,
) -> None:
    """Log a domain event with a conservative field allowlist-by-exclusion."""
    safe_fields = safe_log_fields(fields)
    DOMAIN_EVENT_COUNTER.labels(event=event, level=level).inc()
    if level == "warning":
        logger.warning(event, **safe_fields)
        return
    if level == "error":
        logger.error(event, **safe_fields)
        return
    logger.info(event, **safe_fields)
