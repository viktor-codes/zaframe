"""Claim / clear / persist helpers for order Checkout Sessions."""

from __future__ import annotations

import structlog

from app.core.booking_holds import is_active_pending_hold
from app.core.datetime_utils import utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.integrations.stripe.checkout import build_order_checkout_params
from app.models.booking import BookingStatus
from app.models.order import OrderStatus
from app.models.user import User
from app.modules.payment.access import assert_order_checkout_access
from app.modules.payment.checkout_helpers import (
    OrderCheckoutClaim,
    claim_marker,
    ensure_checkout_claim_available,
    is_stripe_session_id,
    require_connect_account_for_checkout,
)
from app.modules.payment.stripe_client import checkout_session_expires_at, settings

logger = structlog.get_logger(__name__)


async def claim_order_checkout(
    uow: UnitOfWork,
    order_id: int,
    *,
    success_url: str,
    cancel_url: str,
    idempotency_key: str,
    current_user: User | None,
    access_token: str | None,
) -> OrderCheckoutClaim:
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

    marker = claim_marker(idempotency_key)
    ensure_checkout_claim_available(
        existing_session_id=order.checkout_session_id,
        claim_marker_value=marker,
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
    stripe_account_id = require_connect_account_for_checkout(order.studio)
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

    order.checkout_session_id = marker
    await uow.orders.flush()
    await uow.commit()

    return OrderCheckoutClaim(
        order_id=order.id,
        studio_id=order.studio_id,
        claim_marker=marker,
        checkout_params=checkout_params,
        stripe_account_id=stripe_account_id,
    )


async def clear_order_checkout_claim(
    uow: UnitOfWork,
    *,
    order_id: int,
    claim_marker_value: str,
) -> None:
    order = await uow.orders.get_by_id_for_update_with_service_and_studio(order_id)
    if order is None:
        return
    if order.checkout_session_id == claim_marker_value:
        order.checkout_session_id = None
        await uow.orders.flush()
        await uow.commit()


async def persist_order_checkout_session(
    uow: UnitOfWork,
    *,
    order_id: int,
    claim_marker_value: str,
    session_id: str,
    studio_id: int,
    stripe_account_id: str,
) -> None:
    order = await uow.orders.get_by_id_for_update_with_service_and_studio(order_id)
    if order is None:
        raise NotFoundError("Order not found")
    if is_stripe_session_id(order.checkout_session_id):
        if order.checkout_session_id != session_id:
            raise ConflictError("Checkout Session already created for this order")
        return
    if order.checkout_session_id not in (None, claim_marker_value):
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
