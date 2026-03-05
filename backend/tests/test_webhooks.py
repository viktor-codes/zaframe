"""
Тесты для Stripe webhook (app.api.webhooks).

Проверяют все ветки: нет секрета, невалидный payload/подпись, тип события,
order_id/booking_id в metadata, невалидные id, отсутствие metadata.

Интеграционные тесты (mark integration): реальная БД + rollback, webhook
использует ту же сессию, проверка смены статуса.
"""
import hashlib
import hmac
import json
import re
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


def _build_signed_stripe_webhook(
    *,
    booking_id: int | None = None,
    order_id: int | None = None,
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
        "id": "evt_test_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": metadata,
                "payment_intent": "pi_test_123",
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
    captured_url: list[str] = []

    async def capture_email(to: str, url: str) -> None:
        captured_url.append(url)

    with patch("app.services.auth.send_magic_link_email", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = capture_email
        await client.post(
            "/api/v1/auth/magic-link/request",
            json={"email": "webhook-owner@example.com", "name": "Owner"},
        )
    token = re.search(r"token=([^&]+)", captured_url[0]).group(1)
    r_verify = await client.get("/api/v1/auth/magic-link/verify", params={"token": token})
    assert r_verify.status_code == 200
    access = r_verify.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    r_studio = await client.post(
        "/api/v1/studios",
        json={
            "name": "Webhook Studio",
            "description": "For webhook test",
            "email": "wh@example.com",
            "address": "Webhook street 1",
        },
        headers=headers,
    )
    assert r_studio.status_code == 201
    studio_id = r_studio.json()["id"]

    from datetime import datetime, timedelta, timezone

    start = datetime.now(timezone.utc) + timedelta(hours=2)
    end = start + timedelta(hours=1)
    r_slot = await client.post(
        "/api/v1/slots",
        json={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Webhook Slot",
            "description": "Test",
            "max_capacity": 5,
            "price_cents": 1000,
            "studio_id": studio_id,
            "service_id": None,
        },
        headers=headers,
    )
    assert r_slot.status_code == 201
    slot_id = r_slot.json()["id"]

    r_booking = await client.post(
        "/api/v1/bookings",
        json={
            "slot_id": slot_id,
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


def _stripe_event(type: str, metadata: dict | None = None, payment_intent_id: str | None = None):
    """Минимальный объект события Stripe для тестов."""
    obj = MagicMock()
    obj.metadata = metadata or {}
    obj.payment_intent = MagicMock(id=payment_intent_id) if payment_intent_id else None
    event = MagicMock()
    event.type = type
    event.data.object = obj
    return event


@pytest.mark.asyncio
async def test_stripe_webhook_no_secret_returns_500(client):
    """STRIPE_WEBHOOK_SECRET не задан → 500."""
    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = None
        r = await client.post(
            "/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "t=1,v1=abc"},
        )
    assert r.status_code == 500
    assert b"Webhook secret not configured" in r.content


@pytest.mark.asyncio
async def test_stripe_webhook_invalid_payload_returns_400(client):
    """Невалидный payload (ValueError при construct_event) → 400."""
    with patch("app.api.webhooks.settings") as mock_settings:
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

    with patch("app.api.webhooks.settings") as mock_settings:
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
    with patch("app.api.webhooks.settings") as mock_settings:
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
async def test_stripe_webhook_order_id_confirms_order(client):
    """metadata.order_id есть → confirm_order_after_payment, commit, 200."""
    event = _stripe_event("checkout.session.completed", {"order_id": "42"}, "pi_123")
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()
    mock_session = AsyncMock()

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=mock_uow):
                    with patch(
                        "app.api.webhooks.confirm_order_after_payment",
                        new_callable=AsyncMock,
                        return_value=True,
                    ):
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_order_id_invalid_int_returns_200(client):
    """order_id не int (ValueError) → 200 без commit."""
    event = _stripe_event("checkout.session.completed", {"order_id": "not-a-number"})
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=mock_uow):
                    with patch(
                        "app.api.webhooks.confirm_order_after_payment",
                        new_callable=AsyncMock,
                    ) as mock_confirm:
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
    mock_confirm.assert_not_awaited()
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_id_confirms_booking(client):
    """metadata.booking_id есть → confirm_booking_after_payment, commit, 200."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "7"}, "pi_456")
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=mock_uow):
                    with patch(
                        "app.api.webhooks.confirm_booking_after_payment",
                        new_callable=AsyncMock,
                        return_value=True,
                    ):
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
    mock_uow.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_id_invalid_int_returns_200(client):
    """booking_id не int (ValueError) → 200 без вызова confirm_booking."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "nope"})

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=MagicMock()):
                    with patch(
                        "app.api.webhooks.confirm_booking_after_payment",
                        new_callable=AsyncMock,
                    ) as mock_confirm:
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
    mock_confirm.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_no_metadata_returns_200(client):
    """Нет ни booking_id, ни order_id в metadata → 200 (warning в логах)."""
    event = _stripe_event("checkout.session.completed", {})

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=MagicMock()):
                    r = await client.post(
                        "/webhooks/stripe",
                        content=b"{}",
                        headers={"Stripe-Signature": "t=1,v1=x"},
                    )
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_stripe_webhook_order_not_found_returns_200(client):
    """confirm_order_after_payment возвращает False → 200 без commit."""
    event = _stripe_event("checkout.session.completed", {"order_id": "999"})
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=mock_uow):
                    with patch(
                        "app.api.webhooks.confirm_order_after_payment",
                        new_callable=AsyncMock,
                        return_value=False,
                    ):
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
    mock_uow.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_stripe_webhook_booking_not_found_returns_200(client):
    """confirm_booking_after_payment возвращает False → 200 без commit."""
    event = _stripe_event("checkout.session.completed", {"booking_id": "999"})
    mock_uow = MagicMock()
    mock_uow.commit = AsyncMock()

    with patch("app.api.webhooks.settings") as mock_settings:
        mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("app.api.webhooks.async_session_maker") as mock_maker:
                mock_maker.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
                mock_maker.return_value.__aexit__ = AsyncMock(return_value=None)
                with patch("app.api.webhooks.create_uow", return_value=mock_uow):
                    with patch(
                        "app.api.webhooks.confirm_booking_after_payment",
                        new_callable=AsyncMock,
                        return_value=False,
                    ):
                        r = await client.post(
                            "/webhooks/stripe",
                            content=b"{}",
                            headers={"Stripe-Signature": "t=1,v1=x"},
                        )
    assert r.status_code == 200
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
    from app.api import webhooks
    from app.core.uow import create_uow

    booking_id = await _authenticate_and_create_booking(rollback_client)
    session = app_with_rollback_uow.state._integration_session

    class SessionCm:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            pass

    def mock_session_maker():
        return SessionCm()

    def create_uow_no_commit(sess):
        uow = create_uow(sess)
        uow.commit = AsyncMock()
        return uow

    payload, headers = _build_signed_stripe_webhook(booking_id=booking_id)

    with patch.object(webhooks, "async_session_maker", side_effect=mock_session_maker):
        with patch.object(webhooks, "create_uow", side_effect=create_uow_no_commit):
            with patch("app.api.webhooks.settings") as mock_settings:
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

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    assert booking is not None
    assert booking.status == BookingStatus.CONFIRMED


@pytest.mark.integration
@pytest.mark.asyncio
async def test_webhook_order_integration(rollback_client, app_with_rollback_uow):
    """
    Интеграционный тест: создаём заказ (курс) и бронирования, вызываем webhook
    с order_id, проверяем смену статуса заказа и бронирований на paid/confirmed.
    """
    from app.api import webhooks
    from app.core.uow import create_uow
    from app.models.booking import Booking, BookingStatus
    from app.models.order import Order, OrderStatus
    from sqlalchemy import select

    # Создаём пользователя и студию, услугу, слоты, заказ через сервис (минимально)
    booking_id = await _authenticate_and_create_booking(rollback_client)
    session = app_with_rollback_uow.state._integration_session

    # Получаем бронирование и слот, создаём заказ в той же сессии
    from app.models.slot import Slot

    result = await session.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one()
    slot = await session.get(Slot, booking.slot_id)
    assert slot is not None
    order = Order(
        studio_id=slot.studio_id,
        service_id=None,
        user_id=booking.user_id,
        total_amount_cents=1000,
        status=OrderStatus.PENDING,
    )
    session.add(order)
    await session.flush()
    booking.order_id = order.id
    await session.flush()
    order_id = order.id

    class SessionCm:
        async def __aenter__(self):
            return session

        async def __aexit__(self, *args):
            pass

    def mock_session_maker():
        return SessionCm()

    def create_uow_no_commit(sess):
        uow = create_uow(sess)
        uow.commit = AsyncMock()
        return uow

    payload, headers = _build_signed_stripe_webhook(order_id=order_id)

    with patch.object(webhooks, "async_session_maker", side_effect=mock_session_maker):
        with patch.object(webhooks, "create_uow", side_effect=create_uow_no_commit):
            with patch("app.api.webhooks.settings") as mock_settings:
                mock_settings.STRIPE_WEBHOOK_SECRET = "whsec_test"
                r = await rollback_client.post(
                    "/webhooks/stripe",
                    content=payload,
                    headers=headers,
                )
    assert r.status_code == 200

    await session.refresh(order)
    await session.refresh(booking)
    assert order.status == OrderStatus.PAID
    assert booking.status == BookingStatus.CONFIRMED


# --- Юнит-тесты хелперов парсинга ---


def test_parse_checkout_session_metadata_dict():
    """_parse_checkout_session_metadata с dict metadata."""
    from app.api.webhooks import _parse_checkout_session_metadata

    session = MagicMock()
    session.metadata = {"booking_id": "1", "order_id": "2"}
    assert _parse_checkout_session_metadata(session) == ("1", "2")
    session.metadata = {}
    assert _parse_checkout_session_metadata(session) == (None, None)


def test_parse_checkout_session_metadata_object():
    """_parse_checkout_session_metadata с object-like metadata."""
    from app.api.webhooks import _parse_checkout_session_metadata

    session = MagicMock()
    meta = MagicMock()
    meta.booking_id = "b"
    meta.order_id = "o"
    session.metadata = meta
    assert _parse_checkout_session_metadata(session) == ("b", "o")


def test_parse_payment_intent_id():
    """_parse_payment_intent_id извлекает id из payment_intent."""
    from app.api.webhooks import _parse_payment_intent_id

    session = MagicMock()
    session.payment_intent = MagicMock(id="pi_xyz")
    assert _parse_payment_intent_id(session) == "pi_xyz"
    session.payment_intent = None
    assert _parse_payment_intent_id(session) is None


def test_parse_payment_intent_id_dict():
    """_parse_payment_intent_id при session как dict (payment_intent строка)."""
    from app.api.webhooks import _parse_payment_intent_id

    assert _parse_payment_intent_id({"payment_intent": "pi_str"}) == "pi_str"
    assert _parse_payment_intent_id({"payment_intent": None}) is None
