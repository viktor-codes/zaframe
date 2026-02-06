"""
Alembic environment для async миграций.

Почему async миграции:
- Наше приложение использует async SQLAlchemy (AsyncSession)
- Миграции должны работать с теми же настройками, что и приложение
- Используем run_async_migrations из Alembic для поддержки async
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Импортируем Base и settings из нашего приложения
from app.core.config import settings
from app.core.database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Используем Base.metadata для autogenerate миграций.
# Alembic будет автоматически находить все модели, наследующиеся от Base.
target_metadata = Base.metadata

# Переопределяем sqlalchemy.url из config.py вместо alembic.ini
# Это позволяет использовать DATABASE_URL из .env файла
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Это генерирует SQL скрипты без подключения к БД.
    Полезно для проверки миграций перед применением.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Выполняет миграции с переданным соединением."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode с async engine.

    Создаём async engine из настроек и выполняем миграции асинхронно.
    """
    # Создаём async engine из конфигурации Alembic
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Не используем пул для миграций
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Запускает async миграции через asyncio.run().
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
