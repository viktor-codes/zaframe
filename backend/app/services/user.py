"""
Бизнес-логика для пользователей.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Получить пользователя по ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Получить пользователя по email."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_or_create_user(
    db: AsyncSession,
    *,
    email: str,
    name: str,
    phone: str | None = None,
) -> User:
    """
    Получить пользователя по email или создать нового.
    Используется при Magic Link.
    """
    user = await get_user_by_email(db, email)
    if user is not None:
        return user
    user = User(email=email, name=name, phone=phone)
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
