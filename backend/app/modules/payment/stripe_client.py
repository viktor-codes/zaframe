"""Stripe client helpers for Checkout Session creation."""

from __future__ import annotations

from datetime import datetime
from typing import NoReturn

import stripe

from app.core.config import settings
from app.core.datetime_utils import ensure_utc
from app.core.exceptions import AppError

# Stripe Checkout Session minimum lifetime is 30 minutes.
_STRIPE_CHECKOUT_MIN_EXPIRY_SECONDS = 30 * 60

__all__ = [
    "checkout_session_expires_at",
    "get_stripe_client",
    "raise_stripe_app_error",
    "settings",
]


def get_stripe_client() -> stripe.StripeClient:
    """Return Stripe client; raises AppError when the secret key is missing."""
    if not settings.STRIPE_SECRET_KEY:
        raise AppError("STRIPE_SECRET_KEY is not configured", status_code=503)
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


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
