"""
Юнит-тесты для app.services.payment.

Покрывают: create_checkout_session, create_order_checkout_session,
confirm_booking_after_payment, confirm_order_after_payment.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderStatus
from app.models.service import Service
from app.models.slot import Slot
from app.services.payment import (
    confirm_booking_after_payment,
    confirm_order_after_payment,
    create_checkout_session,
    create_order_checkout_session,
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.session = MagicMock()
    uow.session.flush = AsyncMock()
    return uow


# --- create_checkout_session ---


@pytest.mark.asyncio
async def test_create_checkout_session_booking_not_found(mock_uow):
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Бронирование не найдено"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_wrong_status(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.CONFIRMED
    booking.checkout_session_id = None
    booking.slot = MagicMock(spec=Slot)
    booking.slot.price_cents = 1000
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="уже оплачено"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_already_has_session_id(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.checkout_session_id = "cs_old"
    booking.slot = MagicMock(spec=Slot)
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="Checkout Session уже создан"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_slot_price_zero(mock_uow):
    slot = MagicMock(spec=Slot)
    slot.price_cents = 0
    slot.title = "Free"
    slot.description = None
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.checkout_session_id = None
    booking.slot = slot
    booking.guest_email = None
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="не имеет цены"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_no_stripe_key(mock_uow):
    slot = MagicMock(spec=Slot)
    slot.price_cents = 1000
    slot.title = "Paid"
    slot.description = None
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.checkout_session_id = None
    booking.slot = slot
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=booking)
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = None
        with pytest.raises(AppError) as exc_info:
            await create_checkout_session(
                mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
            )
    assert exc_info.value.status_code == 503
    assert "STRIPE_SECRET_KEY" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_create_checkout_session_success(mock_uow):
    slot = MagicMock(spec=Slot)
    slot.price_cents = 1000
    slot.title = "Paid"
    slot.description = "Desc"
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.checkout_session_id = None
    booking.slot = slot
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_slot = AsyncMock(return_value=booking)
    mock_session = MagicMock()
    mock_session.id = "cs_123"
    mock_session.url = "https://checkout.stripe.com/pay"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        with patch(
            "app.services.payment.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_checkout_session(
                mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
            )
    assert result["checkout_url"] == "https://checkout.stripe.com/pay"
    assert result["session_id"] == "cs_123"
    assert booking.checkout_session_id == "cs_123"
    mock_uow.session.flush.assert_awaited_once()


# --- create_order_checkout_session ---


@pytest.mark.asyncio
async def test_create_order_checkout_session_order_not_found(mock_uow):
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Заказ не найден"):
        await create_order_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_wrong_status(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PAID
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "Service"
    order.id = 1
    order.guest_email = None
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=order)
    with pytest.raises(ValidationError, match="уже оплачен"):
        await create_order_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_zero_amount(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 0
    order.service = None
    order.id = 1
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=order)
    with pytest.raises(ValidationError, match="не имеет суммы"):
        await create_order_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_success(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "My Service"
    order.id = 1
    order.guest_email = "o@x.com"
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=order)
    mock_session = MagicMock()
    mock_session.id = "cs_order_1"
    mock_session.url = "https://checkout.stripe.com/order"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        with patch(
            "app.services.payment.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_order_checkout_session(
                mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
            )
    assert result["session_id"] == "cs_order_1"
    assert result["checkout_url"] == "https://checkout.stripe.com/order"
    mock_uow.session.flush.assert_awaited_once()


# --- confirm_booking_after_payment ---


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_not_found(mock_uow):
    mock_uow.bookings.get_by_id = AsyncMock(return_value=None)
    ok = await confirm_booking_after_payment(mock_uow, 999)
    assert ok is False


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_already_confirmed(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.CONFIRMED
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    ok = await confirm_booking_after_payment(mock_uow, 1)
    assert ok is True
    mock_uow.session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_success(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    ok = await confirm_booking_after_payment(
        mock_uow, 1, payment_intent_id="pi_123"
    )
    assert ok is True
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.payment_intent_id == "pi_123"
    mock_uow.session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_success_no_payment_intent(mock_uow):
    """Без payment_intent_id поле payment_intent_id не перезаписывается."""
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.payment_intent_id = None
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    ok = await confirm_booking_after_payment(mock_uow, 1)
    assert ok is True
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.payment_intent_id is None


# --- confirm_order_after_payment ---


@pytest.mark.asyncio
async def test_confirm_order_after_payment_not_found(mock_uow):
    mock_uow.orders.get_by_id = AsyncMock(return_value=None)
    ok = await confirm_order_after_payment(mock_uow, 999)
    assert ok is False


@pytest.mark.asyncio
async def test_confirm_order_after_payment_already_paid(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PAID
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    ok = await confirm_order_after_payment(mock_uow, 1)
    assert ok is True
    mock_uow.bookings.list_.assert_not_called()
    mock_uow.session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_order_after_payment_success_confirms_bookings(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.id = 10
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    b1 = MagicMock(spec=Booking)
    b1.status = BookingStatus.PENDING
    b2 = MagicMock(spec=Booking)
    b2.status = BookingStatus.CONFIRMED
    mock_uow.bookings.list_ = AsyncMock(return_value=[b1, b2])
    ok = await confirm_order_after_payment(
        mock_uow, 10, payment_intent_id="pi_ord"
    )
    assert ok is True
    assert order.status == OrderStatus.PAID
    assert b1.status == BookingStatus.CONFIRMED
    assert b1.payment_status == "succeeded"
    assert b1.payment_intent_id == "pi_ord"
    assert b2.status == BookingStatus.CONFIRMED
    mock_uow.session.flush.assert_awaited_once()
