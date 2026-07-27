"""Shared Stripe Checkout claim markers and session create helpers."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import stripe
from stripe.params.checkout import SessionCreateParams

from app.core.exceptions import ConflictError, ValidationError
from app.models.studio import Studio
from app.modules.payment.stripe_client import get_stripe_client, raise_stripe_app_error, run_stripe

_CONNECT_NOT_READY_MESSAGE = (
    "Paid checkout is unavailable until the studio completes Stripe Connect onboarding"
)
_PENDING_CLAIM_PREFIX = "pending:"


@dataclass(frozen=True, slots=True)
class BookingCheckoutClaim:
    booking_id: int
    occurrence_id: int
    claim_marker: str
    checkout_params: SessionCreateParams
    stripe_account_id: str


@dataclass(frozen=True, slots=True)
class OrderCheckoutClaim:
    order_id: int
    studio_id: int
    claim_marker: str
    checkout_params: SessionCreateParams
    stripe_account_id: str


def require_connect_account_for_checkout(studio: Studio) -> str:
    """Return the destination account for checkout or fail before charging the customer."""
    if studio.stripe_account_id and studio.stripe_charges_enabled:
        return studio.stripe_account_id
    raise ValidationError(_CONNECT_NOT_READY_MESSAGE)


def claim_marker(idempotency_key: str) -> str:
    """
    Fixed-length claim stored in checkout_session_id while Stripe create is in flight.

    WHY: hashed so long Idempotency-Key values fit String(255).
    """
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:40]
    return f"{_PENDING_CLAIM_PREFIX}{digest}"


def is_pending_claim(value: str | None) -> bool:
    return bool(value) and value.startswith(_PENDING_CLAIM_PREFIX)


def is_stripe_session_id(value: str | None) -> bool:
    return bool(value) and not is_pending_claim(value)


def ensure_checkout_claim_available(
    *,
    existing_session_id: str | None,
    claim_marker_value: str,
    already_created_message: str,
) -> None:
    if is_stripe_session_id(existing_session_id):
        raise ValidationError(already_created_message)
    if is_pending_claim(existing_session_id) and existing_session_id != claim_marker_value:
        raise ConflictError("Checkout Session creation already in progress")


async def create_stripe_checkout_session(
    *,
    checkout_params: SessionCreateParams,
    idempotency_key: str,
) -> Any:
    client = get_stripe_client()
    try:
        return await run_stripe(
            lambda: client.v1.checkout.sessions.create(
                params=checkout_params,
                options={"idempotency_key": idempotency_key},
            )
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="checkout session creation")
