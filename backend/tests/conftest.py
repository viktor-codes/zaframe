"""
Общие фикстуры и настройки для тестов backend.

Устанавливаем SECRET_KEY до импорта приложения, чтобы Settings() не падал.
В тестах рейт-лимит по сути отключён (уникальный ключ на запрос).
"""

import os
import sys

import pytest

# Before any `from app.main import app` — Settings() reads env at import time.
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-pytest"
# WHY: checkout-session integration tests mock StripeClient but still call
# get_stripe_client(), which 503s when STRIPE_SECRET_KEY is unset (CI has no .env).
if "STRIPE_SECRET_KEY" not in os.environ:
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_pytest_dummy"
# httpx uses http://test; dev disables Secure cookies for local/test HTTP clients.
os.environ["ENVIRONMENT"] = "dev"


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (needs DB)")
    # В тестах рейт-лимит отключён, чтобы не блокировать множественные запросы к одному эндпоинту
    if "pytest" in sys.modules:
        from app.core.rate_limit import limiter

        limiter.enabled = False


@pytest.fixture
async def app_with_rollback_uow():
    """
    Приложение с подменённым get_uow: одна сессия на тест, rollback в конце.

    Все запросы в рамках одного теста видят одну транзакцию (данные из первого
    запроса доступны во втором). После теста транзакция откатывается — БД не засоряется.
    """
    from sqlalchemy import text

    from app.core.database import async_session_maker, engine
    from app.core.deps import get_uow
    from app.core.uow_factory import uow_scope
    from app.main import app
    from app.models.booking_idempotency_key import BookingIdempotencyKey
    from app.models.processed_webhook_event import ProcessedWebhookEvent

    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: ProcessedWebhookEvent.__table__.create(sync_conn, checkfirst=True)
        )
        await conn.run_sync(
            lambda sync_conn: BookingIdempotencyKey.__table__.create(sync_conn, checkfirst=True)
        )

    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM otp_codes"))
        await session.execute(text("DELETE FROM processed_webhook_events"))
        await session.commit()

        async def get_uow_override():
            # Commit per request so multi-step flows (OTP request → verify) share data;
            # the outer session.rollback() at teardown still cleans up the test DB.
            async with uow_scope(session=session, auto_commit=True) as uow:
                yield uow

        app.dependency_overrides[get_uow] = get_uow_override
        # Для интеграционных тестов webhook: одна и та же сессия на весь тест
        app.state._integration_session = session
        try:
            yield app
        finally:
            await session.rollback()
            app.dependency_overrides.pop(get_uow, None)
            if hasattr(app.state, "_integration_session"):
                del app.state._integration_session


@pytest.fixture
async def client(app_with_rollback_uow):
    """
    HTTP-клиент для интеграционных тестов.

    Использует app с get_uow → rollback: после каждого запроса транзакция
    откатывается, данные не сохраняются в БД.
    """
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(
        transport=ASGITransport(app=app_with_rollback_uow),
        base_url="http://test",
    ) as ac:
        yield ac


async def authenticate_via_otp(
    client,
    *,
    email: str,
    name: str = "Test User",
    booking_id: int | None = None,
) -> dict:
    """
    Request + verify OTP in tests; returns verify JSON (access_token, user, ...).

    Patches send_otp_email to capture the generated code.
    """
    from unittest.mock import patch

    captured_codes: list[str] = []

    async def capture_otp(to: str, code: str) -> bool:
        captured_codes.append(code)
        return True

    with patch("app.modules.auth.otp.send_otp_email", side_effect=capture_otp):
        r_request = await client.post(
            "/api/v1/auth/otp/request",
            json={"email": email, "name": name},
        )
    assert r_request.status_code == 200
    assert len(captured_codes) == 1

    r_verify = await client.post(
        "/api/v1/auth/otp/verify",
        json={
            "email": email,
            "code": captured_codes[0],
            **({"booking_id": booking_id} if booking_id is not None else {}),
        },
    )
    assert r_verify.status_code == 200
    return r_verify.json()


async def create_test_service(
    client,
    *,
    headers: dict[str, str],
    studio_id: int,
    name: str = "Test Service",
    max_capacity: int = 10,
    price_single_cents: int = 1000,
) -> int:
    """Create a published service for tests that need a bookable occurrence."""
    response = await client.post(
        "/api/v1/services",
        json={
            "studio_id": studio_id,
            "name": name,
            "type": "single",
            "duration_minutes": 60,
            "max_capacity": max_capacity,
            "price_single_cents": price_single_cents,
            "visibility": "published",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]
