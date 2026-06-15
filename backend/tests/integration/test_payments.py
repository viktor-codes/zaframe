"""
Integration tests for payments API (Stripe Checkout).

Uses real DB with rollback fixture; Stripe API is mocked.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient
from tests.conftest import authenticate_via_otp

_CHECKOUT_PAYLOAD = {
    "success_url": "https://example.com/payments/success",
    "cancel_url": "https://example.com/payments/cancel",
}


async def _authenticate_user(
    client: AsyncClient,
    email: str,
    name: str = "Test User",
) -> str:
    data = await authenticate_via_otp(client, email=email, name=name)
    return data["access_token"]


async def _create_pending_booking(
    client: AsyncClient,
    *,
    guest_email: str = "guest@example.com",
) -> int:
    """Create owner, studio, occurrence, and guest booking; return booking_id."""
    verify_data = await authenticate_via_otp(
        client,
        email="payments-owner@example.com",
        name="Payments Owner",
    )
    headers = {"Authorization": f"Bearer {verify_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Payments Studio",
            "description": "For payments test",
            "email": "payments@example.com",
            "address": "Payments street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    start = datetime.now(UTC) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/occurrences",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Payments Slot",
            "description": "Test",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": None,
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
    booking = r_booking.json()
    assert booking["status"] == "pending"
    return booking["id"]


def _mock_stripe_checkout_session(
    *,
    session_id: str = "cs_test_123",
    checkout_url: str = "https://checkout.stripe.com/test",
) -> MagicMock:
    mock_session = MagicMock()
    mock_session.id = session_id
    mock_session.url = checkout_url
    mock_client = MagicMock()
    mock_client.v1.checkout.sessions.create.return_value = mock_session
    return mock_client


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkout_session_returns_201_for_pending_booking(client: AsyncClient):
    """POST /payments/checkout-session succeeds with mocked Stripe client."""
    booking_id = await _create_pending_booking(client)
    mock_client = _mock_stripe_checkout_session()

    with patch(
        "app.services.payment.stripe.StripeClient",
        return_value=mock_client,
    ):
        response = await client.post(
            "/api/v1/payments/checkout-session",
            json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
        )

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"checkout_url", "session_id"}
    assert body["checkout_url"] == "https://checkout.stripe.com/test"
    assert body["session_id"] == "cs_test_123"
    mock_client.v1.checkout.sessions.create.assert_called_once()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkout_session_foreign_user_gets_404(client: AsyncClient):
    """Authenticated user cannot create checkout for another guest's booking."""
    booking_id = await _create_pending_booking(client, guest_email="real-guest-pay@example.com")
    stranger_token = await _authenticate_user(client, "stranger-pay-404@example.com")
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    response = await client.post(
        "/api/v1/payments/checkout-session",
        json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
        headers=stranger_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkout_session_authenticated_owner_succeeds(client: AsyncClient):
    """Guest booking owner can checkout after OTP login (guest_email match)."""
    guest_email = "guest-owner-pay@example.com"
    booking_id = await _create_pending_booking(client, guest_email=guest_email)
    guest_token = await _authenticate_user(client, guest_email, name="Guest Owner")
    guest_headers = {"Authorization": f"Bearer {guest_token}"}
    mock_client = _mock_stripe_checkout_session(session_id="cs_owner")

    with patch(
        "app.services.payment.stripe.StripeClient",
        return_value=mock_client,
    ):
        response = await client.post(
            "/api/v1/payments/checkout-session",
            json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
            headers=guest_headers,
        )

    assert response.status_code == 201
    assert response.json()["session_id"] == "cs_owner"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkout_session_rate_limit_returns_429_on_11th_request(client: AsyncClient):
    """11th checkout-session request within a minute is rejected with 429."""
    from app.core.rate_limit import limiter

    limiter.enabled = True
    try:
        for _ in range(10):
            response = await client.post(
                "/api/v1/payments/checkout-session",
                json={"booking_id": 999_999, **_CHECKOUT_PAYLOAD},
            )
            assert response.status_code == 404

        eleventh = await client.post(
            "/api/v1/payments/checkout-session",
            json={"booking_id": 999_999, **_CHECKOUT_PAYLOAD},
        )
        assert eleventh.status_code == 429
    finally:
        limiter.enabled = False


@pytest.mark.integration
@pytest.mark.asyncio
async def test_checkout_session_returns_400_when_session_already_created(client: AsyncClient):
    """Second checkout-session call for the same booking is rejected."""
    booking_id = await _create_pending_booking(client)
    mock_client = _mock_stripe_checkout_session()

    with patch(
        "app.services.payment.stripe.StripeClient",
        return_value=mock_client,
    ):
        first = await client.post(
            "/api/v1/payments/checkout-session",
            json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
        )
        assert first.status_code == 201

        second = await client.post(
            "/api/v1/payments/checkout-session",
            json={"booking_id": booking_id, **_CHECKOUT_PAYLOAD},
        )

    assert second.status_code == 400
    assert "Checkout Session already created" in second.json()["detail"]
