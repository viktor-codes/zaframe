"""Unit tests for payment ledger and refunds."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus, Refund, RefundStatus
from app.modules.payment.ledger import record_checkout_completed_payment
from app.modules.payment.refunds import create_refund_for_payment, update_refund_from_stripe_object


@pytest.fixture
def mock_uow() -> MagicMock:
    uow = MagicMock()
    uow.bookings.get_by_id = AsyncMock(return_value=None)
    uow.orders.get_by_id = AsyncMock(return_value=None)
    uow.payments.get_by_checkout_session_id = AsyncMock(return_value=None)
    uow.payments.get_refund_by_idempotency_key = AsyncMock(return_value=None)
    uow.payments.flush = AsyncMock()
    return uow


@pytest.mark.asyncio
async def test_record_checkout_completed_payment_creates_order_payment(mock_uow: MagicMock) -> None:
    order = MagicMock(spec=Order)
    order.total_amount_cents = 5000
    order.currency = "eur"
    order.payment_intent_id = None
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    captured: list[Payment] = []

    async def add_payment(payment: Payment) -> Payment:
        captured.append(payment)
        return payment

    mock_uow.payments.add = AsyncMock(side_effect=add_payment)

    ok = await record_checkout_completed_payment(
        mock_uow,
        checkout_session_id="cs_123",
        payment_intent_id="pi_123",
        order_id=10,
        amount_cents=5000,
        currency="eur",
    )

    assert ok is True
    assert order.payment_intent_id == "pi_123"
    assert len(captured) == 1
    payment = captured[0]
    assert payment.order_id == 10
    assert payment.stripe_checkout_session_id == "cs_123"
    assert payment.stripe_payment_intent_id == "pi_123"
    assert payment.amount_cents == 5000
    assert payment.status == PaymentStatus.SUCCEEDED


@pytest.mark.asyncio
async def test_create_refund_for_payment_updates_payment_and_order_status(
    mock_uow: MagicMock,
) -> None:
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PAID
    payment = MagicMock(spec=Payment)
    payment.id = 1
    payment.order = order
    payment.booking = None
    payment.amount_cents = 5000
    payment.refunded_amount_cents = 0
    payment.status = PaymentStatus.SUCCEEDED
    payment.stripe_payment_intent_id = "pi_123"

    stripe_refund = MagicMock()
    stripe_refund.id = "re_123"
    stripe_refund.status = "succeeded"
    stripe_refund.created = int(datetime(2026, 6, 19, tzinfo=UTC).timestamp())
    mock_client = MagicMock()
    mock_client.v1.refunds.create.return_value = stripe_refund

    async def add_refund(refund: Refund) -> Refund:
        refund.id = 100
        return refund

    mock_uow.payments.add_refund = AsyncMock(side_effect=add_refund)

    with patch("app.modules.payment.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        with patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ):
            refund = await create_refund_for_payment(
                mock_uow,
                payment=payment,
                amount_cents=None,
                reason="requested_by_customer",
                idempotency_key="refund-key-123",
            )

    assert refund.stripe_refund_id == "re_123"
    assert refund.amount_cents == 5000
    assert payment.refunded_amount_cents == 5000
    assert payment.status == PaymentStatus.REFUNDED
    assert order.status == OrderStatus.REFUNDED
    mock_client.v1.refunds.create.assert_called_once_with(
        params={
            "payment_intent": "pi_123",
            "amount": 5000,
            "reason": "requested_by_customer",
        },
        options={"idempotency_key": "refund-key-123"},
    )
    mock_uow.payments.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_refund_for_payment_pending_refund_does_not_mark_payment_refunded(
    mock_uow: MagicMock,
) -> None:
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PAID
    payment = MagicMock(spec=Payment)
    payment.id = 1
    payment.order = order
    payment.booking = None
    payment.amount_cents = 5000
    payment.refunded_amount_cents = 0
    payment.status = PaymentStatus.SUCCEEDED
    payment.stripe_payment_intent_id = "pi_123"

    stripe_refund = MagicMock()
    stripe_refund.id = "re_pending"
    stripe_refund.status = "pending"
    stripe_refund.created = int(datetime(2026, 6, 19, tzinfo=UTC).timestamp())
    mock_client = MagicMock()
    mock_client.v1.refunds.create.return_value = stripe_refund

    async def add_refund(refund: Refund) -> Refund:
        refund.id = 101
        return refund

    mock_uow.payments.add_refund = AsyncMock(side_effect=add_refund)

    with patch("app.modules.payment.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        with patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ):
            refund = await create_refund_for_payment(
                mock_uow,
                payment=payment,
                amount_cents=2500,
                reason="customer asked nicely",
                idempotency_key="refund-key-pending",
            )

    assert refund.status == "pending"
    assert payment.refunded_amount_cents == 0
    assert payment.status == PaymentStatus.SUCCEEDED
    assert order.status == OrderStatus.PAID


@pytest.mark.asyncio
async def test_create_refund_for_payment_returns_existing_refund_for_same_idempotency_key(
    mock_uow: MagicMock,
) -> None:
    payment = MagicMock(spec=Payment)
    payment.id = 1
    existing_refund = MagicMock(spec=Refund)
    existing_refund.payment_id = 1
    mock_uow.payments.get_refund_by_idempotency_key = AsyncMock(return_value=existing_refund)

    refund = await create_refund_for_payment(
        mock_uow,
        payment=payment,
        amount_cents=1000,
        reason=None,
        idempotency_key="refund-key-existing",
    )

    assert refund is existing_refund
    mock_uow.payments.add_refund.assert_not_called()


@pytest.mark.asyncio
async def test_update_refund_from_stripe_object_applies_succeeded_once(
    mock_uow: MagicMock,
) -> None:
    payment = MagicMock(spec=Payment)
    payment.amount_cents = 5000
    payment.refunded_amount_cents = 0
    payment.status = PaymentStatus.SUCCEEDED
    payment.order = None
    payment.booking = None

    refund = MagicMock(spec=Refund)
    refund.payment = payment
    refund.amount_cents = 2500
    refund.status = RefundStatus.PENDING
    mock_uow.payments.get_refund_by_stripe_refund_id = AsyncMock(return_value=refund)

    stripe_refund = MagicMock()
    stripe_refund.id = "re_123"
    stripe_refund.status = RefundStatus.SUCCEEDED

    first = await update_refund_from_stripe_object(mock_uow, stripe_refund=stripe_refund)
    second = await update_refund_from_stripe_object(mock_uow, stripe_refund=stripe_refund)

    assert first is True
    assert second is True
    assert payment.refunded_amount_cents == 2500
    assert payment.status == PaymentStatus.PARTIALLY_REFUNDED
