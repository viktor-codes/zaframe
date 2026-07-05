"""Payment ledger use-cases."""

from __future__ import annotations

from datetime import datetime

from app.core.datetime_utils import utc_now
from app.core.exceptions import ValidationError
from app.core.uow import UnitOfWork
from app.models.payment import Payment, PaymentProvider, PaymentStatus
from app.modules.payment.stripe_client import settings


def _paid_status(existing_status: str | None = None) -> str:
    if existing_status in {PaymentStatus.REFUNDED, PaymentStatus.PARTIALLY_REFUNDED}:
        return existing_status
    return PaymentStatus.SUCCEEDED


def _payment_status_for_checkout(payment_status: str | None) -> str:
    if payment_status == "paid":
        return PaymentStatus.SUCCEEDED
    if payment_status == "failed":
        return PaymentStatus.FAILED
    return PaymentStatus.PENDING


async def list_studio_payments(
    uow: UnitOfWork,
    *,
    studio_id: int,
    status: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    booking_id: int | None = None,
    order_id: int | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Payment]:
    """Return filtered payments for a studio dashboard."""
    return await uow.payments.list_for_studio(
        studio_id=studio_id,
        status=status,
        start_at=start_at,
        end_at=end_at,
        booking_id=booking_id,
        order_id=order_id,
        skip=skip,
        limit=limit,
    )


async def count_studio_payments(
    uow: UnitOfWork,
    *,
    studio_id: int,
    status: str | None = None,
    start_at: datetime | None = None,
    end_at: datetime | None = None,
    booking_id: int | None = None,
    order_id: int | None = None,
) -> int:
    """Count filtered payments for a studio dashboard."""
    return await uow.payments.count_for_studio(
        studio_id=studio_id,
        status=status,
        start_at=start_at,
        end_at=end_at,
        booking_id=booking_id,
        order_id=order_id,
    )


async def record_checkout_completed_payment(
    uow: UnitOfWork,
    *,
    checkout_session_id: str,
    payment_intent_id: str | None,
    booking_id: int | None = None,
    order_id: int | None = None,
    amount_cents: int | None = None,
    currency: str | None = None,
    payment_status: str | None = "paid",
) -> bool:
    """Create or update a local payment ledger row for a completed checkout session."""
    if booking_id is None and order_id is None:
        raise ValidationError("Payment must reference a booking or order")

    booking = await uow.bookings.get_by_id(booking_id) if booking_id is not None else None
    order = await uow.orders.get_by_id(order_id) if order_id is not None else None
    if booking_id is not None and booking is None:
        return False
    if order_id is not None and order is None:
        return False

    resolved_amount = amount_cents
    resolved_currency = currency
    if order is not None:
        resolved_amount = resolved_amount or order.total_amount_cents
        resolved_currency = resolved_currency or order.currency
        if payment_intent_id:
            order.payment_intent_id = payment_intent_id
    if booking is not None:
        resolved_amount = resolved_amount or booking.unit_price_cents
        resolved_currency = resolved_currency or settings.STRIPE_CURRENCY

    if resolved_amount is None or resolved_amount <= 0:
        raise ValidationError("Payment amount is missing")
    if not resolved_currency:
        raise ValidationError("Payment currency is missing")

    existing = await uow.payments.get_by_checkout_session_id(checkout_session_id)
    if existing is not None:
        existing.booking_id = booking_id
        existing.order_id = order_id
        existing.stripe_payment_intent_id = payment_intent_id
        existing.amount_cents = resolved_amount
        existing.currency = resolved_currency
        existing.provider = PaymentProvider.STRIPE
        existing.status = (
            _paid_status(existing.status)
            if payment_status == "paid"
            else _payment_status_for_checkout(payment_status)
        )
        if payment_status == "paid":
            existing.paid_at = existing.paid_at or utc_now()
        await uow.payments.flush()
        return True

    await uow.payments.add(
        Payment(
            booking_id=booking_id,
            order_id=order_id,
            stripe_checkout_session_id=checkout_session_id,
            stripe_payment_intent_id=payment_intent_id,
            amount_cents=resolved_amount,
            currency=resolved_currency,
            status=_payment_status_for_checkout(payment_status),
            provider=PaymentProvider.STRIPE,
            paid_at=utc_now() if payment_status == "paid" else None,
            refunded_amount_cents=0,
        )
    )
    return True
