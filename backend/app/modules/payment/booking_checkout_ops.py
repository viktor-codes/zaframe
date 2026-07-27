"""Claim / clear / persist helpers for booking Checkout Sessions."""

from __future__ import annotations

import structlog

from app.core.booking_holds import is_active_pending_hold
from app.core.datetime_utils import utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import build_booking_checkout_params
from app.models.booking import BookingStatus
from app.models.user import User
from app.modules.payment.access import assert_booking_checkout_access
from app.modules.payment.checkout_helpers import (
    BookingCheckoutClaim,
    claim_marker,
    ensure_checkout_claim_available,
    is_stripe_session_id,
    require_connect_account_for_checkout,
)
from app.modules.payment.stripe_client import checkout_session_expires_at, settings

logger = structlog.get_logger(__name__)


async def claim_booking_checkout(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None,
    access_token: str | None,
) -> BookingCheckoutClaim:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    assert_booking_checkout_access(
        booking,
        current_user=current_user,
        access_token=access_token,
    )
    if booking.status != BookingStatus.PENDING:
        raise ValidationError("Booking is already paid or cancelled")
    now_utc = utc_now()
    if not is_active_pending_hold(
        status=booking.status,
        reserved_until=booking.reserved_until,
        now=now_utc,
    ):
        raise ValidationError("Booking hold has expired; please book again")

    marker = claim_marker(idempotency_key)
    ensure_checkout_claim_available(
        existing_session_id=booking.checkout_session_id,
        claim_marker_value=marker,
        already_created_message="Checkout Session already created for this booking",
    )

    occurrence = booking.occurrence
    if occurrence.price_cents <= 0:
        raise ValidationError("Occurrence has no price for checkout")

    stripe_account_id = require_connect_account_for_checkout(occurrence.studio)
    checkout_params = build_booking_checkout_params(
        booking_id=booking_id,
        currency=settings.STRIPE_CURRENCY,
        unit_amount_cents=occurrence.price_cents,
        product_name=occurrence.title,
        product_description=occurrence.description or f"Booking occurrence #{occurrence.id}",
        success_url=success_url,
        cancel_url=cancel_url,
        guest_email=booking.guest_email,
        expires_at=checkout_session_expires_at(now_utc),
        stripe_account_id=stripe_account_id,
    )

    booking.checkout_session_id = marker
    await uow.bookings.flush()
    # WHY: release FOR UPDATE before the slow Stripe HTTP call.
    await uow.commit()

    return BookingCheckoutClaim(
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        claim_marker=marker,
        checkout_params=checkout_params,
        stripe_account_id=stripe_account_id,
    )


async def clear_booking_checkout_claim(
    uow: UnitOfWork,
    *,
    booking_id: int,
    claim_marker_value: str,
) -> None:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        return
    if booking.checkout_session_id == claim_marker_value:
        booking.checkout_session_id = None
        await uow.bookings.flush()
        await uow.commit()


async def persist_booking_checkout_session(
    uow: UnitOfWork,
    *,
    booking_id: int,
    claim_marker_value: str,
    session_id: str,
    occurrence_id: int,
    stripe_account_id: str,
) -> None:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    if is_stripe_session_id(booking.checkout_session_id):
        if booking.checkout_session_id != session_id:
            raise ConflictError("Checkout Session already created for this booking")
        return
    if booking.checkout_session_id not in (None, claim_marker_value):
        raise ConflictError("Checkout Session creation already in progress")

    booking.checkout_session_id = session_id
    await uow.bookings.flush()
    await uow.commit()
    log_domain_event(
        logger,
        "checkout_session_created",
        booking_id=booking_id,
        occurrence_id=occurrence_id,
        payment_id=None,
        checkout_session_id=session_id,
        stripe_account_id=stripe_account_id,
    )
