"""Stripe Checkout Session creation for bookings and orders."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

import stripe
import structlog
from stripe.params.checkout import SessionCreateParams

from app.core.booking_holds import is_active_pending_hold
from app.core.datetime_utils import utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import (
    build_booking_checkout_params,
    build_order_checkout_params,
)
from app.models.booking import BookingStatus
from app.models.order import OrderStatus
from app.models.studio import Studio
from app.models.user import User
from app.modules.payment.access import (
    assert_booking_checkout_access,
    assert_order_checkout_access,
)
from app.modules.payment.schemas import validate_checkout_redirect_urls
from app.modules.payment.stripe_client import (
    checkout_session_expires_at,
    get_stripe_client,
    raise_stripe_app_error,
    run_stripe,
    settings,
)

logger = structlog.get_logger(__name__)
_CONNECT_NOT_READY_MESSAGE = (
    "Paid checkout is unavailable until the studio completes Stripe Connect onboarding"
)
_PENDING_CLAIM_PREFIX = "pending:"


@dataclass(frozen=True, slots=True)
class _BookingCheckoutClaim:
    booking_id: int
    occurrence_id: int
    claim_marker: str
    checkout_params: SessionCreateParams
    stripe_account_id: str


@dataclass(frozen=True, slots=True)
class _OrderCheckoutClaim:
    order_id: int
    studio_id: int
    claim_marker: str
    checkout_params: SessionCreateParams
    stripe_account_id: str


def _require_connect_account_for_checkout(studio: Studio) -> str:
    """Return the destination account for checkout or fail before charging the customer."""
    if studio.stripe_account_id and studio.stripe_charges_enabled:
        return studio.stripe_account_id
    raise ValidationError(_CONNECT_NOT_READY_MESSAGE)


def _claim_marker(idempotency_key: str) -> str:
    """
    Fixed-length claim stored in checkout_session_id while Stripe create is in flight.

    WHY: hashed so long Idempotency-Key values fit String(255).
    """
    digest = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest()[:40]
    return f"{_PENDING_CLAIM_PREFIX}{digest}"


def _is_pending_claim(value: str | None) -> bool:
    return bool(value) and value.startswith(_PENDING_CLAIM_PREFIX)


def _is_stripe_session_id(value: str | None) -> bool:
    return bool(value) and not _is_pending_claim(value)


def _ensure_checkout_claim_available(
    *,
    existing_session_id: str | None,
    claim_marker: str,
    already_created_message: str,
) -> None:
    if _is_stripe_session_id(existing_session_id):
        raise ValidationError(already_created_message)
    if _is_pending_claim(existing_session_id) and existing_session_id != claim_marker:
        raise ConflictError("Checkout Session creation already in progress")


async def _create_stripe_checkout_session(
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
    claim = await _claim_booking_checkout(
        uow,
        booking_id,
        success_url=success_url,
        cancel_url=cancel_url,
        idempotency_key=idempotency_key,
        current_user=current_user,
        access_token=access_token,
    )

    try:
        session = await _create_stripe_checkout_session(
            checkout_params=claim.checkout_params,
            idempotency_key=idempotency_key,
        )
    except Exception:
        await _clear_booking_checkout_claim(
            uow,
            booking_id=claim.booking_id,
            claim_marker=claim.claim_marker,
        )
        raise

    await _persist_booking_checkout_session(
        uow,
        booking_id=claim.booking_id,
        claim_marker=claim.claim_marker,
        session_id=session.id,
        occurrence_id=claim.occurrence_id,
        stripe_account_id=claim.stripe_account_id,
    )
    return {"checkout_url": session.url or "", "session_id": session.id}


async def _claim_booking_checkout(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None,
    access_token: str | None,
) -> _BookingCheckoutClaim:
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

    claim_marker = _claim_marker(idempotency_key)
    _ensure_checkout_claim_available(
        existing_session_id=booking.checkout_session_id,
        claim_marker=claim_marker,
        already_created_message="Checkout Session already created for this booking",
    )

    occurrence = booking.occurrence
    if occurrence.price_cents <= 0:
        raise ValidationError("Occurrence has no price for checkout")

    stripe_account_id = _require_connect_account_for_checkout(occurrence.studio)
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

    booking.checkout_session_id = claim_marker
    await uow.bookings.flush()
    # WHY: release FOR UPDATE before the slow Stripe HTTP call.
    await uow.commit()

    return _BookingCheckoutClaim(
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        claim_marker=claim_marker,
        checkout_params=checkout_params,
        stripe_account_id=stripe_account_id,
    )


async def _clear_booking_checkout_claim(
    uow: UnitOfWork,
    *,
    booking_id: int,
    claim_marker: str,
) -> None:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        return
    if booking.checkout_session_id == claim_marker:
        booking.checkout_session_id = None
        await uow.bookings.flush()
        await uow.commit()


async def _persist_booking_checkout_session(
    uow: UnitOfWork,
    *,
    booking_id: int,
    claim_marker: str,
    session_id: str,
    occurrence_id: int,
    stripe_account_id: str,
) -> None:
    booking = await uow.bookings.get_by_id_for_update_with_occurrence_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    if _is_stripe_session_id(booking.checkout_session_id):
        if booking.checkout_session_id != session_id:
            raise ConflictError("Checkout Session already created for this booking")
        return
    if booking.checkout_session_id not in (None, claim_marker):
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
    claim = await _claim_order_checkout(
        uow,
        order_id,
        success_url=success_url,
        cancel_url=cancel_url,
        idempotency_key=idempotency_key,
        current_user=current_user,
        access_token=access_token,
    )

    try:
        session = await _create_stripe_checkout_session(
            checkout_params=claim.checkout_params,
            idempotency_key=idempotency_key,
        )
    except Exception:
        await _clear_order_checkout_claim(
            uow,
            order_id=claim.order_id,
            claim_marker=claim.claim_marker,
        )
        raise

    await _persist_order_checkout_session(
        uow,
        order_id=claim.order_id,
        claim_marker=claim.claim_marker,
        session_id=session.id,
        studio_id=claim.studio_id,
        stripe_account_id=claim.stripe_account_id,
    )
    return {"checkout_url": session.url or "", "session_id": session.id}


async def _claim_order_checkout(
    uow: UnitOfWork,
    order_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None,
    access_token: str | None,
) -> _OrderCheckoutClaim:
    order = await uow.orders.get_by_id_for_update_with_service_and_studio(order_id)
    if order is None:
        raise NotFoundError("Order not found")
    assert_order_checkout_access(
        order,
        current_user=current_user,
        access_token=access_token,
    )
    if order.status != OrderStatus.PENDING:
        raise ValidationError("Order is already paid or cancelled")

    claim_marker = _claim_marker(idempotency_key)
    _ensure_checkout_claim_available(
        existing_session_id=order.checkout_session_id,
        claim_marker=claim_marker,
        already_created_message="Checkout Session already created for this order",
    )

    now_utc = utc_now()
    bookings = await uow.bookings.list_(order_id=order_id, limit=1000)
    for booking in bookings:
        if booking.status != BookingStatus.PENDING:
            continue
        if not is_active_pending_hold(
            status=booking.status,
            reserved_until=booking.reserved_until,
            now=now_utc,
        ):
            raise ValidationError("Booking hold has expired; please book again")

    if order.total_amount_cents <= 0:
        raise ValidationError("Order has no payable amount")

    product_name = order.service.name if order.service is not None else f"Order #{order.id}"
    stripe_account_id = _require_connect_account_for_checkout(order.studio)
    checkout_params = build_order_checkout_params(
        order_id=order_id,
        currency=settings.STRIPE_CURRENCY,
        unit_amount_cents=order.total_amount_cents,
        product_name=product_name,
        product_description=f"Payment for order #{order.id}",
        success_url=success_url,
        cancel_url=cancel_url,
        guest_email=order.guest_email,
        expires_at=checkout_session_expires_at(now_utc),
        stripe_account_id=stripe_account_id,
        application_fee_cents=order.application_fee_cents,
    )

    order.checkout_session_id = claim_marker
    await uow.orders.flush()
    await uow.commit()

    return _OrderCheckoutClaim(
        order_id=order.id,
        studio_id=order.studio_id,
        claim_marker=claim_marker,
        checkout_params=checkout_params,
        stripe_account_id=stripe_account_id,
    )


async def _clear_order_checkout_claim(
    uow: UnitOfWork,
    *,
    order_id: int,
    claim_marker: str,
) -> None:
    order = await uow.orders.get_by_id_for_update_with_service_and_studio(order_id)
    if order is None:
        return
    if order.checkout_session_id == claim_marker:
        order.checkout_session_id = None
        await uow.orders.flush()
        await uow.commit()


async def _persist_order_checkout_session(
    uow: UnitOfWork,
    *,
    order_id: int,
    claim_marker: str,
    session_id: str,
    studio_id: int,
    stripe_account_id: str,
) -> None:
    order = await uow.orders.get_by_id_for_update_with_service_and_studio(order_id)
    if order is None:
        raise NotFoundError("Order not found")
    if _is_stripe_session_id(order.checkout_session_id):
        if order.checkout_session_id != session_id:
            raise ConflictError("Checkout Session already created for this order")
        return
    if order.checkout_session_id not in (None, claim_marker):
        raise ConflictError("Checkout Session creation already in progress")

    order.checkout_session_id = session_id
    await uow.orders.flush()
    await uow.commit()
    log_domain_event(
        logger,
        "checkout_session_created",
        order_id=order_id,
        studio_id=studio_id,
        checkout_session_id=session_id,
        stripe_account_id=stripe_account_id,
    )
