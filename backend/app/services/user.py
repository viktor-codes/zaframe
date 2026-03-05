"""
Бизнес-логика для пользователей.
"""
from app.core.uow import UnitOfWork
from app.models.user import User


async def get_user_by_id(uow: UnitOfWork, user_id: int) -> User | None:
    """Получить пользователя по ID."""
    return await uow.users.get_by_id(user_id)


async def get_user_by_email(uow: UnitOfWork, email: str) -> User | None:
    """Получить пользователя по email."""
    return await uow.users.get_by_email(email)


async def get_or_create_user(
    uow: UnitOfWork,
    *,
    email: str,
    name: str,
    phone: str | None = None,
) -> User:
    """
    Получить пользователя по email или создать нового.
    Используется при Magic Link.
    """
    user = await uow.users.get_by_email(email)
    if user is not None:
        return user
    user = User(email=email, name=name, phone=phone)
    uow.session.add(user)
    await uow.session.flush()
    await uow.session.refresh(user)
    return user
