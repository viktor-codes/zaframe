"""
Unit tests for app.modules.payment.service validation and orchestration.

Checkout payload shape is covered in tests/test_stripe_checkout.py.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppError, ConflictError, NotFoundError, ValidationError
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.models.order import Order, OrderStatus
from app.models.service import Service
from app.models.user import User
from app.modules.payment.service import (
    PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW,
    confirm_booking_after_payment,
    confirm_order_after_payment,
    create_checkout_session,
    create_order_checkout_session,
)


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.bookings.flush = AsyncMock()
    uow.orders.flush = AsyncMock()
    uow.payments.mark_booking_manual_review = AsyncMock(return_value=1)
    uow.payments.mark_order_manual_review = AsyncMock(return_value=1)
    return uow


def _active_hold_until() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=15)


_GUEST_CHECKOUT_TOKEN = "test-guest-checkout-token"
_ORDER_CHECKOUT_TOKEN = "test-order-checkout-token"


def _ready_connect_studio() -> MagicMock:
    studio = MagicMock()
    studio.stripe_account_id = "acct_ready"
    studio.stripe_charges_enabled = True
    return studio


_IDEMPOTENCY_KEY = "test-idempotency-key-01"


def _checkout_kwargs(*, access_token: str = _GUEST_CHECKOUT_TOKEN) -> dict[str, str]:
    return {
        "success_url": "http://localhost:3000/s",
        "cancel_url": "http://localhost:3000/c",
        "access_token": access_token,
        "idempotency_key": _IDEMPOTENCY_KEY,
    }


def _order_checkout_kwargs(*, access_token: str = _ORDER_CHECKOUT_TOKEN) -> dict[str, str]:
    return _checkout_kwargs(access_token=access_token)


def _mock_occurrence_capacity_ok(mock_uow, *, max_capacity: int = 10) -> MagicMock:
    mock_occurrence = MagicMock(spec=Occurrence)
    mock_occurrence.id = 1
    mock_occurrence.max_capacity = max_capacity
    mock_uow.occurrences.get_by_id_for_update = AsyncMock(return_value=mock_occurrence)
    mock_uow.occurrences.get_by_id = AsyncMock(return_value=mock_occurrence)
    mock_uow.bookings.count_confirmed_by_occurrence = AsyncMock(return_value=0)
    mock_uow.bookings.count_pending_by_occurrence = AsyncMock(return_value=0)
    return mock_occurrence


def _mock_order_confirm_batch_capacity(
    mock_uow,
    *,
    occurrences: list[MagicMock],
    counts_map: dict[int, tuple[int, int]] | None = None,
) -> None:
    """Batch capacity mocks for confirm_order_after_payment."""
    by_id = {occ.id: occ for occ in occurrences}

    async def _lock_occurrence(occurrence_id: int) -> MagicMock | None:
        return by_id.get(occurrence_id)

    mock_uow.occurrences.get_by_id_for_update = AsyncMock(side_effect=_lock_occurrence)
    effective_counts = counts_map or {occ.id: (0, 0) for occ in occurrences}
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids = AsyncMock(
        return_value=effective_counts
    )


# --- create_checkout_session ---


@pytest.mark.asyncio
async def test_create_checkout_session_booking_not_found(mock_uow):
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_create_checkout_session_foreign_user_gets_not_found(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.user_id = 99
    booking.guest_email = "other@example.com"
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            current_user=user,
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_create_checkout_session_guest_email_owner_allowed(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 1000
    occurrence.title = "Paid"
    occurrence.description = "Desc"
    occurrence.id = 1
    occurrence.studio = _ready_connect_studio()
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.user_id = None
    booking.guest_email = "me@example.com"
    booking.access_token = "owner-token-not-needed"
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    mock_session = MagicMock()
    mock_session.id = "cs_123"
    mock_session.url = "https://checkout.stripe.com/pay"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.modules.payment.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
        with patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_checkout_session(
                mock_uow,
                1,
                success_url="http://localhost:3000/s",
                cancel_url="http://localhost:3000/c",
                current_user=user,
                idempotency_key=_IDEMPOTENCY_KEY,
            )
    assert result["session_id"] == "cs_123"


@pytest.mark.asyncio
async def test_create_checkout_session_expired_hold(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = datetime.now(UTC) - timedelta(minutes=1)
    booking.checkout_session_id = None
    booking.occurrence = MagicMock(spec=Occurrence)
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="hold has expired"):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_checkout_session_wrong_status(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.CONFIRMED
    booking.checkout_session_id = None
    booking.occurrence = MagicMock(spec=Occurrence)
    booking.occurrence.price_cents = 1000
    booking.guest_email = "g@x.com"
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="already paid or cancelled"):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_checkout_session_already_has_session_id(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = "cs_old"
    booking.occurrence = MagicMock(spec=Occurrence)
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="Checkout Session already created"):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_checkout_session_rejects_foreign_pending_claim(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = "pending:other-claim-marker-0123456789abcdef"
    booking.occurrence = MagicMock(spec=Occurrence)
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with pytest.raises(ConflictError, match="already in progress"):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_checkout_session_slot_price_zero(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 0
    occurrence.title = "Free"
    occurrence.description = None
    occurrence.id = 1
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = None
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with pytest.raises(ValidationError, match="no price for checkout"):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_checkout_session_requires_connect_ready(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 1000
    occurrence.title = "Paid"
    occurrence.description = None
    occurrence.id = 1
    occurrence.studio = MagicMock()
    occurrence.studio.stripe_account_id = None
    occurrence.studio.stripe_charges_enabled = False
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = "g@x.com"
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)

    with (
        patch("app.modules.payment.checkout_helpers.get_stripe_client") as mock_get_client,
        pytest.raises(ValidationError, match="Stripe Connect onboarding"),
    ):
        await create_checkout_session(mock_uow, 1, **_checkout_kwargs())

    mock_get_client.assert_not_called()


@pytest.mark.asyncio
async def test_create_checkout_session_no_stripe_key(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 1000
    occurrence.title = "Paid"
    occurrence.description = None
    occurrence.id = 1
    occurrence.studio = _ready_connect_studio()
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = "g@x.com"
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    with patch("app.modules.payment.stripe_client.settings.STRIPE_SECRET_KEY", None):
        with pytest.raises(AppError) as exc_info:
            await create_checkout_session(mock_uow, 1, **_checkout_kwargs())
    assert exc_info.value.status_code == 503
    assert "STRIPE_SECRET_KEY" in str(exc_info.value.detail)
    assert booking.checkout_session_id is None
    assert mock_uow.commit.await_count == 2


@pytest.mark.asyncio
async def test_create_checkout_session_success(mock_uow):
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 1000
    occurrence.title = "Paid"
    occurrence.description = "Desc"
    occurrence.id = 1
    occurrence.studio = _ready_connect_studio()
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.guest_email = "g@x.com"
    booking.access_token = _GUEST_CHECKOUT_TOKEN
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    mock_session = MagicMock()
    mock_session.id = "cs_123"
    mock_session.url = "https://checkout.stripe.com/pay"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.modules.payment.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
        with patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_checkout_session(
                mock_uow,
                1,
                **_checkout_kwargs(),
            )
    assert result["checkout_url"] == "https://checkout.stripe.com/pay"
    assert result["session_id"] == "cs_123"
    assert booking.checkout_session_id == "cs_123"
    assert mock_uow.bookings.flush.await_count == 2
    assert mock_uow.commit.await_count == 2


# --- create_order_checkout_session ---


@pytest.mark.asyncio
async def test_create_order_checkout_session_order_not_found(mock_uow):
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=None)
    with pytest.raises(NotFoundError, match="Order not found"):
        await create_order_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_create_order_checkout_session_foreign_user_gets_not_found(mock_uow):
    order = MagicMock(spec=Order)
    order.user_id = 99
    order.guest_email = "other@example.com"
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "me@example.com"
    with pytest.raises(NotFoundError, match="Order not found"):
        await create_order_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            current_user=user,
            idempotency_key=_IDEMPOTENCY_KEY,
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
    order.access_token = _ORDER_CHECKOUT_TOKEN
    order.checkout_session_id = None
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    mock_uow.bookings.list_ = AsyncMock(return_value=[expired_booking])
    with pytest.raises(ValidationError, match="hold has expired"):
        await create_order_checkout_session(mock_uow, 1, **_order_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_order_checkout_session_wrong_status(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PAID
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "Service"
    order.id = 1
    order.guest_email = None
    order.access_token = _ORDER_CHECKOUT_TOKEN
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    with pytest.raises(ValidationError, match="already paid or cancelled"):
        await create_order_checkout_session(mock_uow, 1, **_order_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_order_checkout_session_zero_amount(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 0
    order.service = None
    order.id = 1
    order.access_token = _ORDER_CHECKOUT_TOKEN
    order.checkout_session_id = None
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    mock_uow.bookings.list_ = AsyncMock(return_value=[])
    with pytest.raises(ValidationError, match="no payable amount"):
        await create_order_checkout_session(mock_uow, 1, **_order_checkout_kwargs())


@pytest.mark.asyncio
async def test_create_order_checkout_session_requires_connect_ready(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "Service"
    order.id = 1
    order.guest_email = None
    order.access_token = _ORDER_CHECKOUT_TOKEN
    order.checkout_session_id = None
    order.studio = MagicMock()
    order.studio.stripe_account_id = None
    order.studio.stripe_charges_enabled = False
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    active_booking = MagicMock(spec=Booking)
    active_booking.status = BookingStatus.PENDING
    active_booking.reserved_until = _active_hold_until()
    mock_uow.bookings.list_ = AsyncMock(return_value=[active_booking])

    with (
        patch("app.modules.payment.checkout_helpers.get_stripe_client") as mock_get_client,
        pytest.raises(ValidationError, match="Stripe Connect onboarding"),
    ):
        await create_order_checkout_session(mock_uow, 1, **_order_checkout_kwargs())

    mock_get_client.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_checkout_session_rejects_duplicate_session(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.user_id = None
    order.guest_email = None
    order.access_token = _ORDER_CHECKOUT_TOKEN
    order.checkout_session_id = "cs_existing"
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)

    with (
        patch("app.modules.payment.checkout_helpers.get_stripe_client") as mock_get_client,
        pytest.raises(ValidationError, match="Checkout Session already created"),
    ):
        await create_order_checkout_session(mock_uow, 1, **_order_checkout_kwargs())

    mock_get_client.assert_not_called()
    mock_uow.bookings.list_.assert_not_called()


@pytest.mark.asyncio
async def test_create_order_checkout_session_success(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 5000
    order.service = MagicMock(spec=Service)
    order.service.name = "My Service"
    order.id = 1
    order.guest_email = "o@x.com"
    order.access_token = _ORDER_CHECKOUT_TOKEN
    order.checkout_session_id = None
    order.application_fee_cents = None
    order.studio = _ready_connect_studio()
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    active_booking = MagicMock(spec=Booking)
    active_booking.status = BookingStatus.PENDING
    active_booking.reserved_until = _active_hold_until()
    mock_uow.bookings.list_ = AsyncMock(return_value=[active_booking])
    mock_session = MagicMock()
    mock_session.id = "cs_order_1"
    mock_session.url = "https://checkout.stripe.com/order"
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    with patch("app.modules.payment.stripe_client.settings") as mock_settings:
        mock_settings.STRIPE_SECRET_KEY = "sk_test"
        mock_settings.STRIPE_CURRENCY = "usd"
        mock_settings.BOOKING_HOLD_MINUTES = 15
        with patch(
            "app.modules.payment.stripe_client.stripe.StripeClient",
            return_value=mock_client,
        ):
            result = await create_order_checkout_session(
                mock_uow,
                1,
                **_order_checkout_kwargs(),
            )
    assert result["session_id"] == "cs_order_1"
    assert result["checkout_url"] == "https://checkout.stripe.com/order"
    assert order.checkout_session_id == "cs_order_1"
    assert mock_uow.orders.flush.await_count == 2
    assert mock_uow.commit.await_count == 2


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
    _mock_occurrence_capacity_ok(mock_uow)
    ok = await confirm_booking_after_payment(mock_uow, 1, payment_intent_id="pi_123")
    assert ok is True
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.access_token is None
    assert booking.payment_intent_id == "pi_123"
    mock_uow.bookings.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_booking_after_payment_overbooked_manual_review(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.PENDING
    mock_uow.bookings.get_by_id = AsyncMock(return_value=booking)
    _mock_occurrence_capacity_ok(mock_uow, max_capacity=1)
    mock_uow.bookings.count_confirmed_by_occurrence = AsyncMock(return_value=1)
    ok = await confirm_booking_after_payment(mock_uow, 1, payment_intent_id="pi_late")
    assert ok is True
    assert booking.status == BookingStatus.CANCELLED
    assert booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    assert booking.payment_intent_id == "pi_late"
    mock_uow.payments.mark_booking_manual_review.assert_awaited_once_with(
        booking_id=1,
        payment_intent_id="pi_late",
    )
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
    _mock_occurrence_capacity_ok(mock_uow)
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
async def test_confirm_order_after_payment_expired_order_can_confirm_if_capacity_free(mock_uow):
    """Late paid webhook after lifecycle expiry rechecks capacity before reviving seats."""
    order = MagicMock(spec=Order)
    order.status = OrderStatus.EXPIRED
    order.id = 11
    order.access_token = "order-token"
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.EXPIRED
    booking.reserved_until = None
    mock_uow.bookings.list_ = AsyncMock(return_value=[booking])
    occ = MagicMock(spec=Occurrence)
    occ.id = 1
    occ.max_capacity = 1
    _mock_order_confirm_batch_capacity(mock_uow, occurrences=[occ], counts_map={1: (0, 0)})

    ok = await confirm_order_after_payment(mock_uow, 11, payment_intent_id="pi_late_free")

    assert ok is True
    assert order.status == OrderStatus.PAID
    assert order.access_token is None
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.payment_intent_id == "pi_late_free"


@pytest.mark.asyncio
async def test_confirm_order_after_payment_cancelled_order_does_not_revive_bookings(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.CANCELLED
    order.id = 12
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)

    ok = await confirm_order_after_payment(mock_uow, 12, payment_intent_id="pi_cancelled")

    assert ok is True
    assert order.status == OrderStatus.MANUAL_REVIEW
    mock_uow.payments.mark_order_manual_review.assert_awaited_once_with(
        order_id=order.id,
        payment_intent_id="pi_cancelled",
    )
    mock_uow.bookings.list_.assert_not_called()
    mock_uow.orders.flush.assert_awaited_once()


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
    b1.reserved_until = _active_hold_until()
    b2 = MagicMock(spec=Booking)
    b2.id = 2
    b2.occurrence_id = 1
    b2.status = BookingStatus.CONFIRMED
    mock_uow.bookings.list_ = AsyncMock(return_value=[b1, b2])
    occ = MagicMock(spec=Occurrence)
    occ.id = 1
    occ.max_capacity = 10
    _mock_order_confirm_batch_capacity(mock_uow, occurrences=[occ])
    ok = await confirm_order_after_payment(mock_uow, 10, payment_intent_id="pi_ord")
    assert ok is True
    assert order.status == OrderStatus.PAID
    assert b1.status == BookingStatus.CONFIRMED
    assert b1.payment_status == "succeeded"
    assert b1.payment_intent_id == "pi_ord"
    assert b2.status == BookingStatus.CONFIRMED
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids.assert_awaited_once()
    mock_uow.occurrences.get_by_id.assert_not_called()
    mock_uow.bookings.count_confirmed_by_occurrence.assert_not_called()
    mock_uow.bookings.count_pending_by_occurrence.assert_not_called()
    mock_uow.orders.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_confirm_order_after_payment_uses_batch_counts_not_per_booking(mock_uow):
    """Counts are fetched once; no per-booking capacity SQL in the confirm loop."""
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.id = 20
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)

    bookings = []
    occurrences = []
    for idx in range(1, 6):
        booking = MagicMock(spec=Booking)
        booking.id = idx
        booking.occurrence_id = idx
        booking.status = BookingStatus.PENDING
        booking.reserved_until = _active_hold_until()
        bookings.append(booking)
        occ = MagicMock(spec=Occurrence)
        occ.id = idx
        occ.max_capacity = 10
        occurrences.append(occ)

    mock_uow.bookings.list_ = AsyncMock(return_value=bookings)
    _mock_order_confirm_batch_capacity(mock_uow, occurrences=occurrences)

    ok = await confirm_order_after_payment(mock_uow, 20, payment_intent_id="pi_batch")
    assert ok is True
    assert all(b.status == BookingStatus.CONFIRMED for b in bookings)
    mock_uow.bookings.get_confirmed_pending_counts_by_occurrence_ids.assert_awaited_once()
    mock_uow.bookings.count_confirmed_by_occurrence.assert_not_called()
    mock_uow.bookings.count_pending_by_occurrence.assert_not_called()
    mock_uow.occurrences.get_by_id.assert_not_called()


@pytest.mark.asyncio
async def test_confirm_order_after_payment_overbooked_manual_review(mock_uow):
    """Full occurrence → overbooked_manual_review instead of confirm."""
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.id = 30
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    booking = MagicMock(spec=Booking)
    booking.id = 1
    booking.occurrence_id = 1
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    mock_uow.bookings.list_ = AsyncMock(return_value=[booking])
    occ = MagicMock(spec=Occurrence)
    occ.id = 1
    occ.max_capacity = 1
    _mock_order_confirm_batch_capacity(
        mock_uow,
        occurrences=[occ],
        counts_map={1: (1, 1)},
    )
    ok = await confirm_order_after_payment(mock_uow, 30, payment_intent_id="pi_over")
    assert ok is True
    assert order.status == OrderStatus.MANUAL_REVIEW
    assert booking.status == BookingStatus.CANCELLED
    assert booking.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    assert booking.payment_intent_id == "pi_over"
    mock_uow.payments.mark_order_manual_review.assert_awaited_once_with(
        order_id=30,
        payment_intent_id="pi_over",
    )


@pytest.mark.asyncio
async def test_confirm_order_after_payment_two_bookings_same_occurrence_respects_capacity(mock_uow):
    """
    Stale batch counts (0, 1) for two pending bookings: first confirms, second overbooks.

    Local in-memory counter tracks the first confirmation so the second cannot slip through.
    """
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.id = 40
    mock_uow.orders.get_by_id = AsyncMock(return_value=order)
    b1 = MagicMock(spec=Booking)
    b1.id = 1
    b1.occurrence_id = 1
    b1.status = BookingStatus.PENDING
    b1.reserved_until = _active_hold_until()
    b2 = MagicMock(spec=Booking)
    b2.id = 2
    b2.occurrence_id = 1
    b2.status = BookingStatus.PENDING
    b2.reserved_until = _active_hold_until()
    mock_uow.bookings.list_ = AsyncMock(return_value=[b1, b2])
    occ = MagicMock(spec=Occurrence)
    occ.id = 1
    occ.max_capacity = 1
    _mock_order_confirm_batch_capacity(
        mock_uow,
        occurrences=[occ],
        counts_map={1: (0, 1)},
    )
    ok = await confirm_order_after_payment(mock_uow, 40, payment_intent_id="pi_same_occ")
    assert ok is True
    assert order.status == OrderStatus.MANUAL_REVIEW
    assert b1.status == BookingStatus.CONFIRMED
    assert b2.status == BookingStatus.CANCELLED
    assert b2.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    mock_uow.payments.mark_order_manual_review.assert_awaited_once_with(
        order_id=40,
        payment_intent_id="pi_same_occ",
    )
