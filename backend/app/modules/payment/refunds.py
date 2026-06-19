"""Refund use-cases for owner/admin payment actions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal, cast

import stripe
from stripe.params._refund_create_params import RefundCreateParams

from app.core.datetime_utils import utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import BookingStatus
from app.models.order import OrderStatus
from app.models.payment import Payment, PaymentStatus, Refund, RefundStatus
from app.models.studio import Studio
from app.modules.payment.stripe_client import get_stripe_client, raise_stripe_app_error

StripeRefundReason = Literal["duplicate", "fraudulent", "requested_by_customer"]


def _object_value(source: object, key: str) -> object:
    if isinstance(source, dict):
        return cast(dict[str, object], source).get(key)
    return getattr(source, key, None)


def _object_str(source: object, key: str) -> str | None:
    value = _object_value(source, key)
    if value is None:
        return None
    return str(value)


def _created_at_from_refund(refund: object) -> datetime:
    value = _object_value(refund, "created")
    if isinstance(value, int | float):
        return datetime.fromtimestamp(value, UTC)
    return utc_now()


def _apply_succeeded_refund_to_payment(payment: Payment, *, amount_cents: int) -> None:
    payment.refunded_amount_cents += amount_cents
    if payment.refunded_amount_cents >= payment.amount_cents:
        payment.status = PaymentStatus.REFUNDED
        if payment.order is not None:
            payment.order.status = OrderStatus.REFUNDED
        if payment.booking is not None:
            payment.booking.status = BookingStatus.CANCELLED
            payment.booking.payment_status = PaymentStatus.REFUNDED
    else:
        payment.status = PaymentStatus.PARTIALLY_REFUNDED


def _stripe_refund_reason(reason: str | None) -> StripeRefundReason | None:
    if reason == "duplicate":
        return "duplicate"
    if reason == "fraudulent":
        return "fraudulent"
    if reason == "requested_by_customer":
        return "requested_by_customer"
    return None


async def get_payment_or_raise(
    uow: UnitOfWork,
    *,
    payment_id: int,
    for_update: bool = False,
) -> Payment:
    """Fetch payment or raise a domain 404."""
    payment = (
        await uow.payments.get_by_id_for_update(payment_id)
        if for_update
        else await uow.payments.get_by_id(payment_id)
    )
    if payment is None:
        raise NotFoundError("Payment not found")
    return payment


async def get_payment_studio_or_raise(uow: UnitOfWork, *, payment: Payment) -> Studio:
    """Resolve the studio that owns a payment."""
    studio_id: int | None = None
    if payment.order is not None:
        studio_id = payment.order.studio_id
    elif payment.booking is not None:
        studio_id = payment.booking.occurrence.studio_id
    if studio_id is None:
        raise NotFoundError("Payment studio not found")
    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Payment studio not found")
    return studio


def _resolve_refund_amount(payment: Payment, amount_cents: int | None) -> int:
    remaining = payment.amount_cents - payment.refunded_amount_cents
    if remaining <= 0:
        raise ValidationError("Payment is already fully refunded")
    amount = amount_cents or remaining
    if amount <= 0:
        raise ValidationError("Refund amount must be positive")
    if amount > remaining:
        raise ValidationError("Refund amount exceeds refundable amount")
    return amount


async def create_refund_for_payment(
    uow: UnitOfWork,
    *,
    payment: Payment,
    amount_cents: int | None,
    reason: str | None,
    idempotency_key: str,
) -> Refund:
    """Create a Stripe refund and update local payment/order/booking state."""
    existing_refund = await uow.payments.get_refund_by_idempotency_key(idempotency_key)
    if existing_refund is not None:
        if existing_refund.payment_id != payment.id:
            raise ConflictError("Idempotency key is already used for another payment")
        return existing_refund

    if not payment.stripe_payment_intent_id:
        raise ValidationError("Payment has no Stripe PaymentIntent")
    amount = _resolve_refund_amount(payment, amount_cents)

    params: RefundCreateParams = {
        "payment_intent": payment.stripe_payment_intent_id,
        "amount": amount,
    }
    stripe_reason = _stripe_refund_reason(reason)
    if stripe_reason is not None:
        params["reason"] = stripe_reason

    client = get_stripe_client()
    try:
        stripe_refund = client.v1.refunds.create(
            params=params,
            options={"idempotency_key": idempotency_key},
        )
    except stripe.StripeError as e:
        raise_stripe_app_error(e, action="refund creation")
    stripe_refund_id = _object_str(stripe_refund, "id")
    if not stripe_refund_id:
        raise ValidationError("Stripe refund was not created")
    status = _object_str(stripe_refund, "status") or RefundStatus.PENDING

    refund = await uow.payments.add_refund(
        Refund(
            payment_id=payment.id,
            stripe_refund_id=stripe_refund_id,
            idempotency_key=idempotency_key,
            amount_cents=amount,
            reason=reason,
            status=status,
            created_at=_created_at_from_refund(stripe_refund),
        )
    )
    if status == RefundStatus.SUCCEEDED:
        _apply_succeeded_refund_to_payment(payment, amount_cents=amount)

    await uow.payments.flush()
    return refund


async def update_refund_from_stripe_object(uow: UnitOfWork, *, stripe_refund: object) -> bool:
    """Apply a Stripe refund.updated webhook to the local ledger."""
    stripe_refund_id = _object_str(stripe_refund, "id")
    if stripe_refund_id is None:
        return False
    refund = await uow.payments.get_refund_by_stripe_refund_id(stripe_refund_id)
    if refund is None:
        return False

    old_status = refund.status
    new_status = _object_str(stripe_refund, "status") or old_status
    refund.status = new_status
    if old_status != RefundStatus.SUCCEEDED and new_status == RefundStatus.SUCCEEDED:
        _apply_succeeded_refund_to_payment(refund.payment, amount_cents=refund.amount_cents)
    await uow.payments.flush()
    return True
