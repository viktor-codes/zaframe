"""
Tests for guest checkout access tokens (MID-1 IDOR protection).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp, create_test_service

from app.core.exceptions import NotFoundError
from app.core.uow_factory import create_uow
from app.main import app
from app.models.booking import Booking, BookingStatus
from app.models.occurrence import Occurrence
from app.models.order import Order, OrderStatus
from app.modules.payment.service import create_checkout_session, create_order_checkout_session

_CHECKOUT_PAYLOAD = {
    "success_url": "http://localhost:3000/payments/success",
    "cancel_url": "http://localhost:3000/payments/cancel",
}


def _active_hold_until() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=15)


def _mock_stripe_checkout_session(
    *,
    session_id: str = "cs_test_token",
    checkout_url: str = "https://checkout.stripe.com/test",
) -> MagicMock:
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.url = checkout_url
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    return mock_client


async def _create_pending_booking_with_token(
    client: AsyncClient,
    *,
    guest_email: str = "guest-token@example.com",
) -> tuple[int, str]:
    verify_data = await authenticate_via_otp(
        client,
        email="token-owner@example.com",
        name="Token Owner",
    )
    headers = {"Authorization": f"Bearer {verify_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Token Studio",
            "description": "For token test",
            "email": "token@example.com",
            "address": "Token street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    session = app.state._integration_session
    uow = create_uow(session)
    studio = await uow.studios.get_by_id(studio_id)
    assert studio is not None
    studio.stripe_account_id = "acct_ready"
    studio.stripe_charges_enabled = True
    await uow.studios.save(studio)

    service_id = await create_test_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Token Occurrence",
    )

    start = datetime.now(UTC) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/occurrences",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Token Occurrence",
            "description": "Test",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": service_id,
        },
        headers=headers,
    )
    assert r_occurrence.status_code == 201
    occurrence_id = r_occurrence.json()["id"]

    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Guest",
            "guest_email": guest_email,
            "guest_phone": "+111",
        },
    )
    assert r_booking.status_code == 201
    body = r_booking.json()
    assert body["status"] == "pending"
    assert "access_token" in body
    assert body["access_token"]
    return body["id"], body["access_token"]


_IDEMPOTENCY_KEY = "guest-checkout-idem-key"


@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.commit = AsyncMock()
    uow.bookings.flush = AsyncMock()
    uow.orders.flush = AsyncMock()
    return uow


# --- Unit: create_checkout_session access token ---


@pytest.mark.asyncio
async def test_guest_checkout_with_valid_token_succeeds(mock_uow):
    studio = MagicMock()
    studio.stripe_account_id = "acct_ready"
    studio.stripe_charges_enabled = True
    occurrence = MagicMock(spec=Occurrence)
    occurrence.price_cents = 1000
    occurrence.title = "Paid"
    occurrence.description = "Desc"
    occurrence.id = 1
    occurrence.studio = studio
    booking = MagicMock(spec=Booking)
    booking.status = BookingStatus.PENDING
    booking.reserved_until = _active_hold_until()
    booking.checkout_session_id = None
    booking.occurrence = occurrence
    booking.user_id = None
    booking.guest_email = "g@x.com"
    booking.access_token = "valid-secret-token"
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)
    mock_client = _mock_stripe_checkout_session()

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
                access_token="valid-secret-token",
                idempotency_key=_IDEMPOTENCY_KEY,
            )

    assert result["session_id"] == "cs_test_token"
    mock_client.v1.checkout.sessions.create.assert_called_once()


@pytest.mark.asyncio
async def test_guest_checkout_without_token_returns_404(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.user_id = None
    booking.guest_email = "g@x.com"
    booking.access_token = "stored-token"
    booking.occurrence = MagicMock(spec=Occurrence)
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)

    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_guest_checkout_with_wrong_token_returns_404(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.user_id = None
    booking.guest_email = "g@x.com"
    booking.access_token = "stored-token"
    booking.occurrence = MagicMock(spec=Occurrence)
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)

    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            access_token="wrong-token",
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_legacy_booking_without_token_guest_checkout_returns_404(mock_uow):
    booking = MagicMock(spec=Booking)
    booking.user_id = None
    booking.guest_email = "g@x.com"
    booking.access_token = None
    booking.occurrence = MagicMock(spec=Occurrence)
    mock_uow.bookings.get_by_id_for_update_with_occurrence_and_studio = AsyncMock(return_value=booking)

    with pytest.raises(NotFoundError, match="Booking not found"):
        await create_checkout_session(
            mock_uow,
            1,
            success_url="http://localhost:3000/s",
            cancel_url="http://localhost:3000/c",
            access_token="any-token",
            idempotency_key=_IDEMPOTENCY_KEY,
        )


@pytest.mark.asyncio
async def test_order_guest_checkout_with_valid_token_succeeds(mock_uow):
    order = MagicMock(spec=Order)
    order.status = OrderStatus.PENDING
    order.total_amount_cents = 5000
    order.service = MagicMock()
    order.service.name = "Course"
    order.id = 1
    order.guest_email = "o@x.com"
    order.access_token = "order-secret"
    order.checkout_session_id = None
    order.application_fee_cents = 0
    order.studio = MagicMock()
    order.studio.stripe_account_id = "acct_ready"
    order.studio.stripe_charges_enabled = True
    active_booking = MagicMock(spec=Booking)
    active_booking.status = BookingStatus.PENDING
    active_booking.reserved_until = _active_hold_until()
    mock_uow.orders.get_by_id_for_update_with_service_and_studio = AsyncMock(return_value=order)
    mock_uow.bookings.list_ = AsyncMock(return_value=[active_booking])
    mock_client = _mock_stripe_checkout_session(session_id="cs_order_token")

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
                success_url="http://localhost:3000/s",
                cancel_url="http://localhost:3000/c",
                access_token="order-secret",
                idempotency_key=_IDEMPOTENCY_KEY,
            )

    assert result["session_id"] == "cs_order_token"


# --- Integration ---


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_checkout_with_valid_token_succeeds_integration(client: AsyncClient):
    booking_id, access_token = await _create_pending_booking_with_token(client)
    mock_client = _mock_stripe_checkout_session()

    with patch(
        "app.modules.payment.stripe_client.stripe.StripeClient",
        return_value=mock_client,
    ):
        response = await client.post(
            "/api/v1/payments/checkout-session",
            json={
                "booking_id": booking_id,
                "access_token": access_token,
                **_CHECKOUT_PAYLOAD,
            },
            headers={"Idempotency-Key": _IDEMPOTENCY_KEY},
        )

    assert response.status_code == 201
    assert response.json()["session_id"] == "cs_test_token"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_checkout_without_token_returns_404_integration(client: AsyncClient):
    booking_id, _access_token = await _create_pending_booking_with_token(client)

    response = await client.post(
        "/api/v1/payments/checkout-session",
        json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
        headers={"Idempotency-Key": _IDEMPOTENCY_KEY},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_guest_checkout_with_wrong_token_returns_404_integration(client: AsyncClient):
    booking_id, _access_token = await _create_pending_booking_with_token(client)

    response = await client.post(
        "/api/v1/payments/checkout-session",
        json={
            "booking_id": booking_id,
            "access_token": "definitely-wrong-token",
            **_CHECKOUT_PAYLOAD,
        },
        headers={"Idempotency-Key": _IDEMPOTENCY_KEY},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_token_not_leaked_in_list_and_owner_responses(client: AsyncClient):
    guest_email = "leak-check-guest@example.com"
    booking_id, access_token = await _create_pending_booking_with_token(
        client,
        guest_email=guest_email,
    )
    assert access_token

    guest_auth = await authenticate_via_otp(client, email=guest_email, name="Guest Leak")
    guest_headers = {"Authorization": f"Bearer {guest_auth['access_token']}"}

    r_get = await client.get(f"/api/v1/bookings/{booking_id}", headers=guest_headers)
    assert r_get.status_code == 200
    assert "access_token" not in r_get.json()

    r_list = await client.get("/api/v1/bookings/my", headers=guest_headers)
    assert r_list.status_code == 200
    assert r_list.json()["items"]
    for item in r_list.json()["items"]:
        assert "access_token" not in item

    owner_auth = await authenticate_via_otp(
        client,
        email="token-owner@example.com",
        name="Token Owner",
    )
    owner_headers = {"Authorization": f"Bearer {owner_auth['access_token']}"}
    r_owner_list = await client.get("/api/v1/bookings", headers=owner_headers)
    assert r_owner_list.status_code == 200
    for item in r_owner_list.json()["items"]:
        assert "access_token" not in item

    r_owner_get = await client.get(f"/api/v1/bookings/{booking_id}", headers=owner_headers)
    assert r_owner_get.status_code == 200
    assert "access_token" not in r_owner_get.json()
