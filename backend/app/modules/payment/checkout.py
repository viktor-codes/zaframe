"""Stripe Checkout Session creation for bookings and orders."""

from __future__ import annotations

from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.payment.booking_checkout_ops import (
    claim_booking_checkout,
    clear_booking_checkout_claim,
    persist_booking_checkout_session,
)
from app.modules.payment.checkout_helpers import create_stripe_checkout_session
from app.modules.payment.order_checkout_ops import (
    claim_order_checkout,
    clear_order_checkout_claim,
    persist_order_checkout_session,
)
from app.modules.payment.schemas import validate_checkout_redirect_urls


async def create_checkout_session(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None = None,
    access_token: str | None = None,
) -> dict[str, str]:
    """
    Create Stripe Checkout Session for a booking payment.

    Authenticated callers must own the booking (user_id or guest_email).
    Guest callers must supply the access_token from booking create response.
    Legacy bookings without a token require authenticated owner access.

    Flow: row lock + claim commit → Stripe outside locks → persist session id.
    Idempotency-Key is required and forwarded to Stripe.

    Returns: {"checkout_url": "...", "session_id": "..."}
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    claim = await claim_booking_checkout(
        uow,
        booking_id,
        success_url=success_url,
        cancel_url=cancel_url,
        idempotency_key=idempotency_key,
        current_user=current_user,
        access_token=access_token,
    )

    try:
        session = await create_stripe_checkout_session(
            checkout_params=claim.checkout_params,
            idempotency_key=idempotency_key,
        )
    except Exception:
        await clear_booking_checkout_claim(
            uow,
            booking_id=claim.booking_id,
            claim_marker_value=claim.claim_marker,
        )
        raise

    await persist_booking_checkout_session(
        uow,
        booking_id=claim.booking_id,
        claim_marker_value=claim.claim_marker,
        session_id=session.id,
        occurrence_id=claim.occurrence_id,
        stripe_account_id=claim.stripe_account_id,
    )
    return {"checkout_url": session.url or "", "session_id": session.id}


async def create_order_checkout_session(
    uow: UnitOfWork,
    order_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None = None,
    access_token: str | None = None,
) -> dict[str, str]:
    """
    Create Stripe Checkout Session for an order payment.

    Authenticated callers must own the order (user_id or guest_email).
    Guest callers must supply the access_token from course order create response.
    Legacy orders without a token require authenticated owner access.

    Amount comes from order.total_amount_cents; order_id is stored in session metadata.
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    claim = await claim_order_checkout(
        uow,
        order_id,
        success_url=success_url,
        cancel_url=cancel_url,
        idempotency_key=idempotency_key,
        current_user=current_user,
        access_token=access_token,
    )

    try:
        session = await create_stripe_checkout_session(
            checkout_params=claim.checkout_params,
            idempotency_key=idempotency_key,
        )
    except Exception:
        await clear_order_checkout_claim(
            uow,
            order_id=claim.order_id,
            claim_marker_value=claim.claim_marker,
        )
        raise

    await persist_order_checkout_session(
        uow,
        order_id=claim.order_id,
        claim_marker_value=claim.claim_marker,
        session_id=session.id,
        studio_id=claim.studio_id,
        stripe_account_id=claim.stripe_account_id,
    )
    return {"checkout_url": session.url or "", "session_id": session.id}
