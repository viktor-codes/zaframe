"""
Общие фикстуры и настройки для тестов backend.

Устанавливаем SECRET_KEY до импорта приложения, чтобы Settings() не падал.
В тестах рейт-лимит по сути отключён (уникальный ключ на запрос).
"""
import os
import sys

import pytest

# До импорта app — иначе settings не найдёт SECRET_KEY
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-pytest"


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
    from app.main import app
    from app.api.deps import get_uow
    from app.core.database import async_session_maker
    from app.core.uow import create_uow

    async with async_session_maker() as session:
        async def get_uow_override():
            uow = create_uow(session)
            yield uow
            # Не коммитим — в конце теста делаем rollback

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
