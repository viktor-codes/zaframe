"""Stripe Checkout Session creation for bookings and orders."""

from __future__ import annotations

import stripe
import structlog

from app.core.booking_holds import is_active_pending_hold
from app.core.datetime_utils import utc_now
from app.core.exceptions import NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import (
    build_booking_checkout_params,
    build_order_checkout_params,
)
from app.models.booking import BookingStatus
from app.models.occurrence import Occurrence
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
    settings,
)

logger = structlog.get_logger(__name__)
_CONNECT_NOT_READY_MESSAGE = (
    "Paid checkout is unavailable until the studio completes Stripe Connect onboarding"
)


def _require_connect_account_for_checkout(studio: Studio) -> str:
    """Return the destination account for checkout or fail before charging the customer."""
    if studio.stripe_account_id and studio.stripe_charges_enabled:
        return studio.stripe_account_id
    raise ValidationError(_CONNECT_NOT_READY_MESSAGE)


async def create_checkout_session(
    uow: UnitOfWork,
    booking_id: int,
    *,
    success_url: str,
    cancel_url: str,
    current_user: User | None = None,
    access_token: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """
    Create Stripe Checkout Session for a booking payment.

    Authenticated callers must own the booking (user_id or guest_email).
    Guest callers must supply the access_token from booking create response.
    Legacy bookings without a token require authenticated owner access.

    Returns: {"checkout_url": "...", "session_id": "..."}
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    booking = await uow.bookings.get_by_id_with_occurrence_and_studio(booking_id)
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
    if booking.checkout_session_id:
        raise ValidationError("Checkout Session already created for this booking")

    occurrence: Occurrence = booking.occurrence
    if occurrence.price_cents <= 0:
        raise ValidationError("Occurrence has no price for checkout")

    studio = occurrence.studio
    stripe_account_id = _require_connect_account_for_checkout(studio)
    client = get_stripe_client()
    try:
        session = client.v1.checkout.sessions.create(
            params=build_booking_checkout_params(
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
            ),
            options={"idempotency_key": idempotency_key} if idempotency_key else None,
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="checkout session creation")

    booking.checkout_session_id = session.id
    await uow.bookings.flush()
    log_domain_event(
        logger,
        "checkout_session_created",
        booking_id=booking.id,
        occurrence_id=booking.occurrence_id,
        payment_id=None,
        checkout_session_id=session.id,
        stripe_account_id=stripe_account_id,
    )

    return {"checkout_url": session.url or "", "session_id": session.id}


async def create_order_checkout_session(
    uow: UnitOfWork,
    order_id: int,
    *,
    success_url: str,
    cancel_url: str,
    current_user: User | None = None,
    access_token: str | None = None,
    idempotency_key: str | None = None,
) -> dict[str, str]:
    """
    Create Stripe Checkout Session for an order payment.

    Authenticated callers must own the order (user_id or guest_email).
    Guest callers must supply the access_token from course order create response.
    Legacy orders without a token require authenticated owner access.

    Amount comes from order.total_amount_cents; order_id is stored in session metadata.
    """
    validate_checkout_redirect_urls(success_url, cancel_url)
    order = await uow.orders.get_by_id_with_service_and_studio(order_id)
    if order is None:
        raise NotFoundError("Order not found")
    assert_order_checkout_access(
        order,
        current_user=current_user,
        access_token=access_token,
    )
    if order.status != OrderStatus.PENDING:
        raise ValidationError("Order is already paid or cancelled")

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

    product_name = order.service.name if order.service is not None else f"Заказ #{order.id}"
    stripe_account_id = _require_connect_account_for_checkout(order.studio)

    client = get_stripe_client()
    try:
        session = client.v1.checkout.sessions.create(
            params=build_order_checkout_params(
                order_id=order_id,
                currency=settings.STRIPE_CURRENCY,
                unit_amount_cents=order.total_amount_cents,
                product_name=product_name,
                product_description=f"Оплата заказа #{order.id}",
                success_url=success_url,
                cancel_url=cancel_url,
                guest_email=order.guest_email,
                expires_at=checkout_session_expires_at(now_utc),
                stripe_account_id=stripe_account_id,
                application_fee_cents=order.application_fee_cents,
            ),
            options={"idempotency_key": idempotency_key} if idempotency_key else None,
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="checkout session creation")

    await uow.orders.flush()
    log_domain_event(
        logger,
        "checkout_session_created",
        order_id=order.id,
        studio_id=order.studio_id,
        checkout_session_id=session.id,
        stripe_account_id=stripe_account_id,
    )

    return {"checkout_url": session.url or "", "session_id": session.id}
