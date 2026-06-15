"""
Unit tests for app.services.payment validation and orchestration.

Checkout payload shape is covered in tests/test_stripe_checkout.py.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppError, NotFoundError, ValidationError
from app.models.booking import Booking, BookingStatus
from app.models.order import Order, OrderStatus
from app.models.service import Service
from app.models.occurrence import Occurrence
from app.models.user import User
from app.services.payment import (
    PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW,
    confirm_booking_after_payment,
    confirm_order_after_payment,
    create_checkout_session,
    create_order_checkout_session,
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.bookings.flush = AsyncMock()
    uow.orders.flush = AsyncMock()
    return uow


def _active_hold_until() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=15)


def _mock_slot_capacity_ok(mock_uow, *, max_capacity: int = 10) -> MagicMock:
    mock_occurrence = MagicMock(spec=Occurrence)
    mock_slot.id = 1
    mock_slot.max_capacity = max_capacity
    mock_uow.occurrences.get_by_id_for_update = AsyncMock(return_value=mock_slot)
    mock_uow.occurrences.get_by_id = AsyncMock(return_value=mock_slot)
    mock_uow.bookings.count_confirmed_by_occurrence = AsyncMock(return_value=0)
    mock_uow.bookings.count_pending_by_occurrence = AsyncMock(return_value=0)
    return mock_occurrence


# --- create_checkout_session ---


@pytest.mark.asyncio
async def test_create_checkout_session_booking_not_found(mock_uow):
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_foreign_user_gets_not_found(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.user_id = 99
    booking.guest_email = "other@example.com"
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="https://a/s",
            cancel_url="https://a/c",
            current_user=user,
        )


@pytest.mark.asyncio
async def test_create_checkout_session_guest_email_owner_allowed(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    slot.price_cents = 1000
    slot.title = "Paid"
    slot.description = "Desc"
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.user_id = None
    booking.guest_email = "me@example.com"
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    mock_session = MagicMock()
    mock_session.id = "cs_123"
    mock_session.url = "https://checkout.stripe.com/pay"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
        with patch(
            "app.services.payment.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_checkout_session(
                mock_uow,
                1,
                success_url="https://a/s",
                cancel_url="https://a/c",
                current_user=user,
            )
    assert result["session_id"] == "cs_123"


@pytest.mark.asyncio
async def test_create_checkout_session_expired_hold(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = datetime.now(UTC) - timedelta(minutes=1)
    booking.checkout_session_id = None
    booking.occurrence = MagicMock(spec=Occurrence)
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="hold has expired"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_wrong_status(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.CONFIRMED
    booking.checkout_session_id = None
    booking.occurrence = MagicMock(spec=Occurrence)
    booking.occurrence.price_cents = 1000
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="already paid or cancelled"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_already_has_session_id(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = "cs_old"
    booking.occurrence = MagicMock(spec=Occurrence)
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="Checkout Session already created"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_slot_price_zero(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    slot.price_cents = 0
    slot.title = "Free"
    slot.description = None
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = None
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="no price for checkout"):
        await create_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_checkout_session_no_stripe_key(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    slot.price_cents = 1000
    slot.title = "Paid"
    slot.description = None
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
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
    occurrence = MagicMock(spec=Occurrence)
    slot.price_cents = 1000
    slot.title = "Paid"
    slot.description = "Desc"
    slot.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = "g@x.com"
    mock_uow.bookings.get_by_id_with_occurrence = AsyncMock(return_value=booking)
    mock_session = MagicMock()
    mock_session.id = "cs_123"
    mock_session.url = "https://checkout.stripe.com/pay"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
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
    mock_uow.bookings.flush.assert_awaited_once()


# --- create_order_checkout_session ---


@pytest.mark.asyncio
async def test_create_order_checkout_session_order_not_found(mock_uow):
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Order not found"):
        await create_order_checkout_session(
            mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_foreign_user_gets_not_found(mock_uow):
    order = MagicMock(spec=Order)
    order.user_id = 99
    order.guest_email = "other@example.com"
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=order)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    with pytest.raises(NotFoundError, match="Order not found"):
        await create_order_checkout_session(
            mock_uow,
            1,
            success_url="https://a/s",
            cancel_url="https://a/c",
            current_user=user,
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_expired_hold(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "Service"
    order.id = 1
    order.guest_email = None
    expired_booking = MagicMock(spec=Booking)
    expired_booking.status = BookingStatus.PENDING
    expired_booking.reserved_until = datetime.now(UTC) - timedelta(minutes=1)
    mock_uow.orders.get_by_id_with_service = AsyncMock(return_value=order)
    mock_uow.bookings.list_ = AsyncMock(return_value=[expired_booking])
    with pytest.raises(ValidationError, match="hold has expired"):
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
    with pytest.raises(ValidationError, match="already paid or cancelled"):
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
    mock_uow.bookings.list_ = AsyncMock(return_value=[])
    with pytest.raises(ValidationError, match="no payable amount"):
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
    active_booking = MagicMock(spec=Booking)
    active_booking.status = BookingStatus.PENDING
    active_booking.reserved_until = _active_hold_until()
    mock_uow.bookings.list_ = AsyncMock(return_value=[active_booking])
    mock_session = MagicMock()
    mock_session.id = "cs_order_1"
    mock_session.url = "https://checkout.stripe.com/order"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.services.payment.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
        with patch(
            "app.services.payment.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_order_checkout_session(
                mock_uow, 1, success_url="https://a/s", cancel_url="https://a/c"
            )
    assert result["session_id"] == "cs_order_1"
    assert result["checkout_url"] == "https://checkout.stripe.com/order"
    mock_uow.orders.flush.assert_awaited_once()


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
    mock_uow.bookings.flush.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_success(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.PENDING
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    _mock_slot_capacity_ok(mock_uow)
    ok = await confirm_booking_after_payment(mock_uow, 1, payment_intent_id="pi_123")
    assert ok is True
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.payment_intent_id == "pi_123"
    mock_uow.bookings.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_overbooked_manual_review(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.PENDING
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    _mock_slot_capacity_ok(mock_uow, max_capacity=1)
    mock_uow.bookings.count_confirmed_by_occurrence = AsyncMock(return_value=1)
    ok = await confirm_booking_after_payment(mock_uow, 1, payment_intent_id="pi_late")
    assert ok is True
    assert booking.status == BookingStatus.CANCELLED
    assert booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    assert booking.payment_intent_id == "pi_late"
    mock_uow.bookings.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_success_no_payment_intent(mock_uow):
    """Without payment_intent_id the field is not overwritten."""
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.PENDING
    booking.payment_intent_id = None
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    _mock_slot_capacity_ok(mock_uow)
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
    mock_uow.orders.flush.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_order_after_payment_success_confirms_bookings(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.id = 10
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    b1 = MagicMock(spec=Booking)
    b1.id = 1
    b1.occurrence_id = 1
    b1.status = BookingStatus.PENDING
    b2 = MagicMock(spec=Booking)
    b2.id = 2
    b2.occurrence_id = 1
    b2.status = BookingStatus.CONFIRMED
    mock_uow.bookings.list_ = AsyncMock(return_value=[b1, b2])
    _mock_slot_capacity_ok(mock_uow)
    ok = await confirm_order_after_payment(mock_uow, 10, payment_intent_id="pi_ord")
    assert ok is True
    assert order.status == OrderStatus.PAID
    assert b1.status == BookingStatus.CONFIRMED
    assert b1.payment_status == "succeeded"
    assert b1.payment_intent_id == "pi_ord"
    assert b2.status == BookingStatus.CONFIRMED
    mock_uow.orders.flush.assert_awaited_once()
