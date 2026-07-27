"""Stripe client helpers: network policy and non-blocking async facade."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import NoReturn

import stripe
from stripe._http_client import RequestsClient

from app.core.config import settings
from app.core.datetime_utils import ensure_utc
from app.core.exceptions import AppError, ServiceUnavailableError

# Stripe Checkout Session minimum lifetime is 30 minutes.
_STRIPE_CHECKOUT_MIN_EXPIRY_SECONDS = 30 * 60
_STRIPE_HTTP_TIMEOUT_SECONDS = 15.0
_STRIPE_MAX_NETWORK_RETRIES = 2

__all__ = [
    "checkout_session_expires_at",
    "get_stripe_client",
    "raise_stripe_app_error",
    "run_stripe",
    "settings",
]


def get_stripe_client() -> stripe.StripeClient:
    """Return Stripe client with explicit timeout and retry policy."""
    if not settings.STRIPE_SECRET_KEY:
        raise ServiceUnavailableError("STRIPE_SECRET_KEY is not configured")
    return stripe.StripeClient(
        api_key=settings.STRIPE_SECRET_KEY,
        max_network_retries=_STRIPE_MAX_NETWORK_RETRIES,
        # WHY: default Requests timeout is 80s — too long for an API worker under load.
        http_client=RequestsClient(timeout=_STRIPE_HTTP_TIMEOUT_SECONDS),
    )


async def run_stripe[T](operation: Callable[[], T]) -> T:
    """
    Run a blocking Stripe SDK call off the event loop.

    Callers must catch stripe.StripeError and map via raise_stripe_app_error.
    """
    return await asyncio.to_thread(operation)


def raise_stripe_app_error(error: stripe.StripeError, *, action: str) -> NoReturn:
    """Map Stripe SDK failures to a safe application error."""
    raise AppError(f"Stripe {action} failed", status_code=502) from error


def checkout_session_expires_at(now: datetime) -> int:
    """
    Unix timestamp for Stripe Checkout Session expires_at.

    Aligns with BOOKING_HOLD_MINUTES but respects Stripe's 30-minute minimum.
    """
    hold_seconds = settings.BOOKING_HOLD_MINUTES * 60
    expiry_seconds = max(hold_seconds, _STRIPE_CHECKOUT_MIN_EXPIRY_SECONDS)
    return int(ensure_utc(now).timestamp()) + expiry_seconds
