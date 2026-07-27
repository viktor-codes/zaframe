"""
Тесты для Stripe webhook (app.modules.payment.webhooks).

Проверяют все ветки: нет секрета, невалидный payload/подпись, тип события,
order_id/booking_id в metadata, невалидные id, отсутствие metadata.

Интеграционные тесты (mark integration): реальная БД + rollback, webhook
использует ту же сессию, проверка смены статуса.
"""

import hashlib
import hmac
import json
import time
from contextlib import asynccontextmanager
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from tests.conftest import authenticate_via_otp, create_test_service

from app.main import app


def _build_signed_stripe_webhook(
    *,
    booking_id: int | None = None,
    order_id: int | None = None,
    event_id: str = "evt_test_1",
    secret: str = "whsec_test",
) -> tuple[bytes, dict]:
    """
    Собирает payload события checkout.session.completed и подпись для Stripe.

    Возвращает (body, headers) для POST /webhooks/stripe.
    """
    metadata = {}
    if booking_id is not None:
        metadata["booking_id"] = str(booking_id)
    if order_id is not None:
        metadata["order_id"] = str(order_id)
    event = {
        "id": event_id,
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_123",
                "metadata": metadata,
                "payment_intent": "pi_test_123",
                "amount_total": 1000,
                "currency": "eur",
                "payment_status": "paid",
            }
        },
    }
    payload = json.dumps(event).encode("utf-8")
    timestamp = int(time.time())
    signed = f"{timestamp}.{payload.decode()}"
    sig = hmac.new(
        secret.encode(),
        signed.encode(),
        hashlib.sha256,
    ).hexdigest()
    return payload, {"Stripe-Signature": f"t={timestamp},v1={sig}"}


async def _authenticate_and_create_booking(client: AsyncClient) -> int:
    """Создаёт пользователя, студию, слот и гостевое бронирование. Возвращает booking_id."""
    verify_data = await authenticate_via_otp(
        client,
        email="webhook-owner@example.com",
        name="Owner",
    )
    access = verify_data["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Webhook Studio",
            "description": "For webhook test",
            "email": "wh@example.com",
            "address": "Webhook street 1",
            "timezone": "Europe/Dublin",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]
    service_id = await create_test_service(
        client,
        headers=headers,
        studio_id=studio_id,
        name="Webhook Occurrence",
    )

    from datetime import datetime, timedelta

    start = datetime.now(UTC) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_occurrence = await client.post(
        "/api/v1/occurrences",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Webhook Occurrence",
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
            "guest_email": "guest@example.com",
            "guest_phone": "+111",
        },
    )
    assert r_booking.status_code == 201
    return r_booking.json()["id"]


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


def _stripe_event(
    type: str,
    metadata: dict | None = None,
    payment_intent_id: str | None = None,
    event_id: str = "evt_test_1",
    payment_status: str = "paid",
):
    """Минимальный объект события Stripe для тестов."""
    obj = MagicMock()
    obj.id = "cs_test_123"
    obj.metadata = metadata or {}
    obj.payment_intent = MagicMock(id=payment_intent_id) if payment_intent_id else None
    obj.amount_total = 1000
    obj.currency = "eur"
    obj.payment_status = payment_status
    event = MagicMock()
    event.id = event_id
    event.type = type
    event.data.object = obj
    return event


def _mock_webhook_uow(*, duplicate_event: bool = False) -> MagicMock:
    """UnitOfWork mock with webhook idempotency ledger."""
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()
    mock_uow.rollback = AsyncMock()
    mock_uow.webhook_events = MagicMock()
    mock_uow.webhook_events.exists_by_event_id = AsyncMock(return_value=duplicate_event)
    mock_uow.webhook_events.record = AsyncMock()
    mock_order = MagicMock()
    mock_order.total_amount_cents = 1000
    mock_order.currency = "eur"
    mock_uow.orders.get_by_id = AsyncMock(return_value=mock_order)
    mock_booking = MagicMock()
    mock_booking.unit_price_cents = 1000
    mock_uow.bookings.get_by_id = AsyncMock(return_value=mock_booking)
    mock_uow.payments.get_by_checkout_session_id = AsyncMock(return_value=None)
    mock_uow.payments.add = AsyncMock()
    mock_uow.payments.flush = AsyncMock()
    return mock_uow


@asynccontextmanager
async def _mock_uow_scope(uow: MagicMock, **kwargs):
    yield uow


@pytest.mark.asyncio
async def test_stripe_webhook_no_secret_returns_503(client):
    """STRIPE_WEBHOOK_SECRET не задан → 503."""
    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = None
        r = await client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "t=1,v1=abc"},
        )
    assert r.status_code == 503
    assert b"Webhook secret not configured" in r.content


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_payload_returns_400(client):
    """Невалидный payload (ValueError при construct_event) → 400."""
    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", side_effect=ValueError("bad payload")):
            r = await client.post(
                "/webhooks/stripe",
                content=b"not json",
                headers={"Stripe-Signature": "t=1,v1=abc"},
            )
    assert r.status_code == 400
    assert b"Invalid payload" in r.content


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_signature_returns_400(client):
    """Невалидная подпись → 400."""
    import stripe

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError("bad sig", "SigHeader"),
        ):
            r = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"Stripe-Signature": "invalid"},
            )
    assert r.status_code == 400
    assert b"Invalid signature" in r.content


@pytest.mark.asyncio
async def test_stripe_webhook_other_event_type_returns_200(client):
    """Тип события != checkout.session.completed → 200 без вызова сервисов."""
    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch(
            "stripe.Webhook.construct_event",
            return_value=_stripe_event("payment_intent.succeeded", {}),
        ):
            r = await client.post(
                "/webhooks/stripe",
                content=b"{}",
                headers={"Stripe-Signature": "t=1,v1=x"},
            )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_stripe_webhook_account_updated_updates_connect_status(client):
    """account.updated → обновляет Connect статус студии и пишет processed event."""
    event = _stripe_event("account.updated", event_id="evt_account_1")
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_handlers.update_studio_connect_status_from_account",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_update:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )

    assert r.status_code == 200
    mock_update.assert_awaited_once()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_account_1",
        event_type="account.updated",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_refund_updated_updates_refund_status(client):
    """refund.updated → обновляет локальный Refund/Payment ledger."""
    event = _stripe_event("refund.updated", event_id="evt_refund_1")
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_handlers.update_refund_from_stripe_object",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_update:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )

    assert r.status_code == 200
    mock_update.assert_awaited_once()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_refund_1",
        event_type="refund.updated",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_account_updated_unmatched_records_event(client):
    """Unmatched account.updated is recorded so supported events are not silently lost."""
    event = _stripe_event("account.updated", event_id="evt_account_unmatched")
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_handlers.update_studio_connect_status_from_account",
                    new_callable=AsyncMock,
                    return_value=False,
                ):
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )

    assert r.status_code == 200
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_account_unmatched",
        event_type="account.updated",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_order_id_confirms_order(client):
    """metadata.order_id есть → confirm_order_after_payment, commit, 200."""
    event = _stripe_event("checkout.session.completed", {"order_id": "42"}, "pi_123")
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_order_after_payment",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200
    mock_confirm.assert_awaited_once()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_test_1",
        event_type="checkout.session.completed",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_unpaid_checkout_does_not_confirm_order(client):
    """checkout.session.completed with unpaid payment_status records ledger but does not confirm."""
    event = _stripe_event(
        "checkout.session.completed",
        {"order_id": "42"},
        "pi_123",
        payment_status="unpaid",
    )
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_order_after_payment",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )

    assert r.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_uow.payments.add.assert_awaited_once()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_test_1",
        event_type="checkout.session.completed",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_order_id_invalid_int_returns_200(client):
    """order_id не int (ValueError) → 200 and record ignored outcome."""
    event = _stripe_event("checkout.session.completed", {"order_id": "not-a-number"})
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_order_after_payment",
                    new_callable=AsyncMock,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_test_1",
        event_type="checkout.session.completed",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_id_confirms_booking(client):
    """metadata.booking_id есть → confirm_booking_after_payment, commit, 200."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "7"}, "pi_456")
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                    new_callable=AsyncMock,
                    return_value=True,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200
    mock_confirm.assert_awaited_once()
    mock_uow.webhook_events.record.assert_awaited_once()
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_id_invalid_int_returns_200(client):
    """booking_id не int (ValueError) → 200 and record ignored outcome."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "nope"})
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                    new_callable=AsyncMock,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_test_1",
        event_type="checkout.session.completed",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_no_metadata_returns_200(client):
    """Нет ни booking_id, ни order_id в metadata → 200 and record ignored outcome."""
    event = _stripe_event("checkout.session.completed", {})
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                r = await client.post(
                    "/webhooks/stripe",
                    content=b"{}",
                    headers={"Stripe-Signature": "t=1,v1=x"},
                )
    assert r.status_code == 200
    mock_uow.webhook_events.record.assert_awaited_once_with(
        event_id="evt_test_1",
        event_type="checkout.session.completed",
    )
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_order_not_found_returns_503(client):
    """confirm_order_after_payment returns False → 503 so Stripe retries."""
    event = _stripe_event("checkout.session.completed", {"order_id": "999"})
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_order_after_payment",
                    new_callable=AsyncMock,
                    return_value=False,
                ):
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 503
    mock_uow.webhook_events.record.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_not_found_returns_503(client):
    """confirm_booking_after_payment returns False → 503 so Stripe retries."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "999"})
    mock_uow = _mock_webhook_uow()

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                    new_callable=AsyncMock,
                    return_value=False,
                ):
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 503
    mock_uow.webhook_events.record.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_ledger_unavailable_returns_503(client):
    """Missing booking for ledger → 503 without recording processed event."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "999"}, "pi_456")
    mock_uow = _mock_webhook_uow()
    mock_uow.bookings.get_by_id = AsyncMock(return_value=None)

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                    new_callable=AsyncMock,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 503
    mock_confirm.assert_not_awaited()
    mock_uow.webhook_events.record.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_duplicate_event_skips_confirm(client):
    """Повторная доставка того же event.id → 200 без повторного confirm."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "7"}, event_id="evt_dup_1")
    mock_uow = _mock_webhook_uow(duplicate_event=True)

    with patch("app.modules.payment.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch(
                "app.modules.payment.webhooks.uow_scope",
                side_effect=lambda **kw: _mock_uow_scope(mock_uow, **kw),
            ):
                with patch(
                    "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                    new_callable=AsyncMock,
                ) as mock_confirm:
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_uow.webhook_events.record.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


# --- Интеграционные тесты (реальная БД + одна сессия, rollback в конце) ---


@pytest.fixture
async def rollback_client(app_with_rollback_uow):
    """Клиент с app, у которого get_uow подменён на одну сессию с rollback."""
    async with AsyncClient(
        transport=ASGITransport(app=app_with_rollback_uow),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_booking_integration(rollback_client, app_with_rollback_uow):
    """
    Интеграционный тест: создаём бронирование, вызываем webhook с валидной подписью,
    проверяем смену статуса на confirmed в той же сессии (commit — no-op, rollback в конце).
    """
    from app.core.uow_factory import create_uow
    from app.modules.payment import webhooks

    booking_id = await _authenticate_and_create_booking(rollback_client)
    integration_session = app_with_rollback_uow.state._integration_session

    @asynccontextmanager
    async def integration_uow_scope(*, session=None, auto_commit=True):
        active_session = session if session is not None else integration_session
        uow = create_uow(active_session)
        uow.commit = AsyncMock()
        yield uow

    payload, headers = _build_signed_stripe_webhook(booking_id=booking_id)

    with patch.object(webhooks, "uow_scope", side_effect=integration_uow_scope):
        with patch("app.modules.payment.webhooks.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
            r = await rollback_client.post(
                "/webhooks/stripe",
                content=payload,
                headers=headers,
            )
    assert r.status_code == 200

    # В той же сессии бронирование должно быть confirmed
    from sqlalchemy import select

    from app.models.booking import Booking, BookingStatus
    from app.models.processed_webhook_event import ProcessedWebhookEvent

    result = await integration_session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    assert booking is not None
    assert booking.status == BookingStatus.CONFIRMED

    processed = await integration_session.execute(
        select(ProcessedWebhookEvent).where(ProcessedWebhookEvent.event_id == "evt_test_1")
    )
    assert processed.scalar_one_or_none() is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_order_integration(rollback_client, app_with_rollback_uow):
    """
    Интеграционный тест: создаём заказ (курс) и бронирования, вызываем webhook
    с order_id, проверяем смену статуса заказа и бронирований на paid/confirmed.
    """
    from sqlalchemy import select

    from app.core.uow_factory import create_uow
    from app.models.booking import Booking, BookingStatus
    from app.models.order import Order, OrderStatus
    from app.modules.payment import webhooks

    # Создаём пользователя и студию, услугу, слоты, заказ через сервис (минимально)
    booking_id = await _authenticate_and_create_booking(rollback_client)
    integration_session = app_with_rollback_uow.state._integration_session

    # Получаем бронирование и слот, создаём заказ в той же сессии
    from app.models.occurrence import Occurrence

    result = await integration_session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one()
    occurrence = await integration_session.get(Occurrence, booking.occurrence_id)
    assert occurrence is not None
    order = Order(
        studio_id=occurrence.studio_id,
        service_id=None,
        user_id=booking.user_id,
        total_amount_cents=1000,
        status=OrderStatus.PENDING,
    )
    integration_session.add(order)
    await integration_session.flush()
    booking.order_id = order.id
    await integration_session.flush()
    order_id = order.id

    @asynccontextmanager
    async def integration_uow_scope(*, session=None, auto_commit=True):
        active_session = session if session is not None else integration_session
        uow = create_uow(active_session)
        uow.commit = AsyncMock()
        yield uow

    payload, headers = _build_signed_stripe_webhook(order_id=order_id)

    with patch.object(webhooks, "uow_scope", side_effect=integration_uow_scope):
        with patch("app.modules.payment.webhooks.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
            r = await rollback_client.post(
                "/webhooks/stripe",
                content=payload,
                headers=headers,
            )
    assert r.status_code == 200

    await integration_session.refresh(order)
    await integration_session.refresh(booking)
    assert order.status == OrderStatus.PAID
    assert booking.status == BookingStatus.CONFIRMED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_duplicate_event_integration(rollback_client, app_with_rollback_uow):
    """
    Повторная доставка того же event.id не вызывает повторного подтверждения.
    """
    from sqlalchemy import func, select

    from app.core.uow_factory import create_uow
    from app.models.booking import Booking, BookingStatus
    from app.models.processed_webhook_event import ProcessedWebhookEvent
    from app.modules.payment import service as payment_service
    from app.modules.payment import webhooks

    booking_id = await _authenticate_and_create_booking(rollback_client)
    integration_session = app_with_rollback_uow.state._integration_session
    event_id = "evt_integration_dup"

    @asynccontextmanager
    async def integration_uow_scope(*, session=None, auto_commit=True):
        active_session = session if session is not None else integration_session
        uow = create_uow(active_session)
        uow.commit = AsyncMock()
        yield uow

    payload, headers = _build_signed_stripe_webhook(booking_id=booking_id, event_id=event_id)

    with patch.object(webhooks, "uow_scope", side_effect=integration_uow_scope):
        with patch("app.modules.payment.webhooks.settings") as mock_settings:
            mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
            with patch(
                "app.modules.payment.webhook_paid_checkout.confirm_booking_after_payment",
                wraps=payment_service.confirm_booking_after_payment,
            ) as mock_confirm:
                r1 = await rollback_client.post(
                    "/webhooks/stripe",
                    content=payload,
                    headers=headers,
                )
                r2 = await rollback_client.post(
                    "/webhooks/stripe",
                    content=payload,
                    headers=headers,
                )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert mock_confirm.await_count == 1

    result = await integration_session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one()
    assert booking.status == BookingStatus.CONFIRMED

    count_result = await integration_session.execute(
        select(func.count())
        .select_from(ProcessedWebhookEvent)
        .where(ProcessedWebhookEvent.event_id == event_id)
    )
    assert int(count_result.scalar_one()) == 1


# --- Юнит-тесты хелперов парсинга ---


def testparse_checkout_session_metadata_dict():
    """parse_checkout_session_metadata с dict metadata."""
    from app.modules.payment.webhook_processor import parse_checkout_session_metadata

    session = MagicMock()
    session.metadata = {"booking_id": "1", "order_id": "2"}
    assert parse_checkout_session_metadata(session) == ("1", "2")
    session.metadata = {}
    assert parse_checkout_session_metadata(session) == (None, None)


def testparse_checkout_session_metadata_object():
    """parse_checkout_session_metadata с object-like metadata."""
    from app.modules.payment.webhook_processor import parse_checkout_session_metadata

    session = MagicMock()
    meta = MagicMock()
    meta.booking_id = "b"
    meta.order_id = "o"
    session.metadata = meta
    assert parse_checkout_session_metadata(session) == ("b", "o")


def testparse_payment_intent_id():
    """parse_payment_intent_id извлекает id из payment_intent."""
    from app.modules.payment.webhook_processor import parse_payment_intent_id

    session = MagicMock()
    session.payment_intent = MagicMock(id="pi_xyz")
    assert parse_payment_intent_id(session) == "pi_xyz"
    session.payment_intent = None
    assert parse_payment_intent_id(session) is None


def testparse_payment_intent_id_dict():
    """parse_payment_intent_id при session как dict (payment_intent строка)."""
    from app.modules.payment.webhook_processor import parse_payment_intent_id

    assert parse_payment_intent_id({"payment_intent": "pi_str"}) == "pi_str"
    assert parse_payment_intent_id({"payment_intent": None}) is None
