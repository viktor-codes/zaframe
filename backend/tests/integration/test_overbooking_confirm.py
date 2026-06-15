"""
Integration tests: overbooking guard on payment confirmation (webhook).

Variant 1: recheck slot capacity under row lock before CONFIRMED.
Variant 2: Checkout Session expires_at aligned with hold window (Stripe min 30 min).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from tests.conftest import authenticate_via_otp

from app.models.booking import Booking, BookingStatus
from app.services.payment import PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW


def _build_signed_stripe_webhook(
    *,
    booking_id: int | None = None,
    payment_intent: str = "pi_test_overbook",
    event_id: str | None = None,
    secret: str = "whsec_test",
) -> tuple[bytes, dict]:
    metadata: dict[str, str] = {}
    if booking_id is not None:
        metadata["booking_id"] = str(booking_id)
    event = {
        "id": event_id or f"evt_{uuid.uuid4().hex}",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": metadata,
                "payment_intent": payment_intent,
            }
        },
    }
    payload = json.dumps(event).encode("utf-8")
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload.decode()}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return payload, {"Stripe-Signature": f"t={timestamp},v1={sig}"}


async def _create_studio_and_slot(
    client: AsyncClient,
    *,
    owner_email: str,
    max_capacity: int = 1,
) -> tuple[int, int]:
    """Return (occurrence_id, studio_id)."""
    verify_data = await authenticate_via_otp(
        client,
        email=owner_email,
        name="Overbook Owner",
    )
    headers = {"Authorization": f"Bearer {verify_data['access_token']}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Overbook Studio",
            "description": "Capacity tests",
            "email": "overbook@example.com",
            "address": "Overbook street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    start = datetime.now(UTC) + timedelta(hours=3)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/slots",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Overbook Slot",
            "description": "Single seat",
            "max_capacity": max_capacity,
            "price_cents": 2000,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=headers,
    )
    assert r_slot.status_code == 201
    return r_slot.json()["id"], studio_id


async def _create_guest_booking(client: AsyncClient, occurrence_id: int, *, email: str) -> int:
    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "occurrence_id": occurrence_id,
            "guest_name": "Guest",
            "guest_email": email,
            "guest_phone": "+100",
        },
    )
    assert r_booking.status_code == 201
    return r_booking.json()["id"]


async def _post_booking_webhook(
    client: AsyncClient,
    app,
    *,
    booking_id: int,
    payment_intent: str = "pi_test_overbook",
    event_id: str | None = None,
) -> int:
    from contextlib import asynccontextmanager

    from app.core.uow import create_uow

    integration_session = app.state._integration_session
    effective_event_id = event_id or f"evt_{uuid.uuid4().hex}"
    payload, headers = _build_signed_stripe_webhook(
        booking_id=booking_id,
        payment_intent=payment_intent,
        event_id=effective_event_id,
    )

    @asynccontextmanager
    async def integration_uow_scope(*, session=None, auto_commit=True):
        # WHY: no real commit — keeps processed_webhook_events inside session rollback.
        uow = create_uow(integration_session)
        uow.commit = AsyncMock()
        yield uow

    with patch("app.api.webhooks.uow_scope", integration_uow_scope):
        with patch("app.api.webhooks.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
            r = await client.post(
                "/webhooks/stripe",
                content=payload,
                headers=headers,
            )
    return r.status_code


@pytest.fixture
async def rollback_client(app_with_rollback_uow):
    async with AsyncClient(
        transport=ASGITransport(app=app_with_rollback_uow),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.integration
@pytest.mark.asyncio
async def test_expired_hold_payment_does_not_overbook_slot(
    rollback_client, app_with_rollback_uow
):
    """
    max_capacity=1: booking A (expired hold) + booking B (confirmed).
    Webhook for A must not create a second confirmed seat; A → manual review.
    """
    occurrence_id, _ = await _create_studio_and_slot(
        rollback_client,
        owner_email="overbook-a@example.com",
        max_capacity=1,
    )
    booking_a_id = await _create_guest_booking(
        rollback_client, occurrence_id, email="guest-a@example.com"
    )

    session = app_with_rollback_uow.state._integration_session

    # Expire A's hold (simulate 15+ min without checkout completion).
    result = await session.execute(select(Booking).where(Booking.id == booking_a_id))
    booking_a = result.scalar_one()
    booking_a.reserved_until = datetime.now(UTC) - timedelta(minutes=1)
    await session.flush()

    booking_b_id = await _create_guest_booking(
        rollback_client, occurrence_id, email="guest-b@example.com"
    )

    # B pays and confirms while A's hold no longer reserves capacity.
    assert (
        await _post_booking_webhook(
            rollback_client,
            app_with_rollback_uow,
            booking_id=booking_b_id,
            payment_intent="pi_b_confirmed",
        )
        == 200
    )

    result = await session.execute(select(Booking).where(Booking.id == booking_b_id))
    booking_b = result.scalar_one()
    assert booking_b.status == BookingStatus.CONFIRMED

    # Late payment webhook for A must not confirm the seat.
    with patch("stripe.StripeClient") as mock_stripe_cls:
        mock_stripe_cls.return_value.v1.refunds.create = MagicMock()
        status = await _post_booking_webhook(
            rollback_client,
            app_with_rollback_uow,
            booking_id=booking_a_id,
            payment_intent="pi_a_late",
        )
    assert status == 200

    await session.refresh(booking_a)
    assert booking_a.status == BookingStatus.CANCELLED
    assert booking_a.payment_status == PAYMENT_STATUS_OVERBOOKED_MANUAL_REVIEW
    assert booking_a.payment_intent_id == "pi_a_late"

    confirmed_count = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.occurrence_id == occurrence_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    assert confirmed_count == 1

    mock_stripe_cls.return_value.v1.refunds.create.assert_not_called()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_repeated_webhook_on_confirmed_booking_is_idempotent(
    rollback_client, app_with_rollback_uow
):
    """Second checkout.session.completed for an already confirmed booking changes nothing."""
    occurrence_id, _ = await _create_studio_and_slot(
        rollback_client,
        owner_email="overbook-idem@example.com",
        max_capacity=1,
    )
    booking_id = await _create_guest_booking(
        rollback_client, occurrence_id, email="idem@example.com"
    )

    session = app_with_rollback_uow.state._integration_session
    event_id = f"evt_{uuid.uuid4().hex}"

    for _ in range(2):
        assert (
            await _post_booking_webhook(
                rollback_client,
                app_with_rollback_uow,
                booking_id=booking_id,
                payment_intent="pi_idem",
                event_id=event_id,
            )
            == 200
        )

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one()
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.payment_status == "succeeded"
    assert booking.payment_intent_id == "pi_idem"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_two_pending_within_hold_both_confirm_when_capacity_allows(
    rollback_client, app_with_rollback_uow
):
    """Inside active hold window, two pending bookings on max_capacity=2 both confirm."""
    occurrence_id, _ = await _create_studio_and_slot(
        rollback_client,
        owner_email="overbook-hold@example.com",
        max_capacity=2,
    )
    booking_a_id = await _create_guest_booking(
        rollback_client, occurrence_id, email="hold-a@example.com"
    )
    booking_b_id = await _create_guest_booking(
        rollback_client, occurrence_id, email="hold-b@example.com"
    )

    session = app_with_rollback_uow.state._integration_session

    for bid, pi in (
        (booking_a_id, "pi_hold_a"),
        (booking_b_id, "pi_hold_b"),
    ):
        assert (
            await _post_booking_webhook(
                rollback_client,
                app_with_rollback_uow,
                booking_id=bid,
                payment_intent=pi,
            )
            == 200
        )

    confirmed_count = await session.scalar(
        select(func.count())
        .select_from(Booking)
        .where(
            Booking.occurrence_id == occurrence_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    assert confirmed_count == 2
