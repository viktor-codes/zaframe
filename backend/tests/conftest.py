"""
Общие фикстуры и настройки для тестов backend.

Устанавливаем SECRET_KEY до импорта приложения, чтобы Settings() не падал.
"""
import os

# До импорта app — иначе settings не найдёт SECRET_KEY
if "SECRET_KEY" not in os.environ:
    os.environ["SECRET_KEY"] = "test-secret-key-min-32-chars-for-pytest"


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark test as integration (needs DB)")


async def _get_test_db():
    """Сессия БД с откатом транзакции после каждого запроса."""
    from collections.abc import AsyncGenerator
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.core.database import engine

    conn = await engine.connect()
    trans = await conn.begin()
    session = AsyncSession(bind=conn, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await trans.rollback()
        await conn.close()
