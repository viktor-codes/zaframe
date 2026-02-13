"""
Настройка подключения к PostgreSQL через SQLAlchemy 2.0 (async).

Почему asyncpg:
- Асинхронный драйвер для PostgreSQL, работает с asyncio
- Высокая производительность для I/O операций
- Поддерживает connection pooling из коробки

Почему SQLAlchemy 2.0 AsyncSession:
- Официальная поддержка async/await в SQLAlchemy 2.0
- Использует create_async_engine вместо create_engine
- AsyncSession вместо Session для всех операций с БД

Почему DeclarativeBase:
- Новая база для моделей в SQLAlchemy 2.0 (вместо declarative_base)
- Поддерживает type hints через Mapped и mapped_column
- Совместим с async операциями
"""
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# === Engine: пул соединений к БД ===
# create_async_engine создаёт асинхронный engine с connection pooling.
# pool_pre_ping=True — проверяет соединения перед использованием (автовосстановление).
# echo=settings.DEBUG — логирует SQL запросы в режиме отладки.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Проверка соединений перед использованием
    pool_size=20,          # Увеличиваем количество постоянных соединений
    max_overflow=10,      # Сколько можно открыть сверх лимита в пике
    pool_timeout=30,      # Сколько ждать свободного слота
    pool_recycle=3600,    # Пересоздавать соединение раз в час
    echo=settings.DEBUG,  # Логирование SQL в режиме отладки
)



# === Session Factory ===
# async_sessionmaker создаёт фабрику для AsyncSession.
# expire_on_commit=False — объекты остаются доступными после commit (удобно для FastAPI).
# class_=AsyncSession — явно указываем класс сессии.
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Объекты остаются доступными после commit
)


# === Base для моделей ===
# DeclarativeBase — база для всех ORM моделей.
# Все модели будут наследоваться от этого класса.
# Используется в app/models/*.py
class Base(DeclarativeBase):
    pass


# === Dependency для FastAPI ===
# Функция-зависимость для получения сессии БД в роутерах.
# Используется через Depends(get_db) в эндпоинтах.
# Гарантирует закрытие сессии после использования (через yield).
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД в роутерах.
    
    Использование:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()  # Коммит при успешном выполнении
        except Exception:
            await session.rollback()  # Откат при ошибке
            raise
        finally:
            await session.close()  # Закрытие сессии
