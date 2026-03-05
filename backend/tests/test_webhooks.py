"""
Тесты для Stripe webhook (app.api.webhooks).

Проверяют все ветки: нет секрета, невалидный payload/подпись, тип события,
order_id/booking_id в metadata, невалидные id, отсутствие metadata.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


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
