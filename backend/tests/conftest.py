"""
Общие фикстуры и настройки для тестов backend.

Устанавливаем SECRET_KEY до импорта приложения, чтобы Settings() не падал.
"""
import os

import pytest

# До импорта app — иначе settings не найдёт SECRET_KEY
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-pytest"


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (needs DB)")


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
        try:
            yield app
        finally:
            await session.rollback()
            app.dependency_overrides.pop(get_uow, None)


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
