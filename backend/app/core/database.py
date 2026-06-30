"""
PostgreSQL connection setup through SQLAlchemy 2.0 async APIs.

Why asyncpg:
- Async PostgreSQL driver that works with asyncio
- Strong performance for I/O-bound operations
- Supports connection pooling out of the box

Why SQLAlchemy 2.0 AsyncSession:
- Official async/await support in SQLAlchemy 2.0
- Uses create_async_engine instead of create_engine
- Uses AsyncSession instead of Session for all DB operations

Why DeclarativeBase:
- Modern SQLAlchemy 2.0 base class for models instead of declarative_base
- Supports type hints through Mapped and mapped_column
- Compatible with async operations
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# === Engine: database connection pool ===
# create_async_engine creates an async engine with connection pooling.
# pool_pre_ping=True checks connections before use for automatic recovery.
# echo=settings.DEBUG logs SQL queries in debug mode.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connections before use
    pool_size=20,  # Number of persistent connections
    max_overflow=10,  # Extra connections allowed during bursts
    pool_timeout=30,  # Seconds to wait for an available connection
    pool_recycle=3600,  # Recreate connections once per hour
    echo=settings.DEBUG,  # Log SQL in debug mode
)


# === Session Factory ===
# async_sessionmaker creates a factory for AsyncSession.
# expire_on_commit=False keeps objects available after commit, which fits FastAPI handlers.
# class_=AsyncSession explicitly selects the session class.
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Objects remain available after commit
)


# === Base for models ===
# DeclarativeBase is the base for all ORM models.
# All models inherit from this class.
# Used in app/models/*.py
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency for obtaining a DB session in routers.

    Usage:
        from typing import Annotated

        @router.get("/users")
        async def get_users(db: Annotated[AsyncSession, Depends(get_db)]):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        yield session
