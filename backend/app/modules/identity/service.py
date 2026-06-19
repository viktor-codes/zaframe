"""
Бизнес-логика для пользователей.
"""

from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.identity.schemas import CurrentUserUpdate


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
    Get user by email or create a new one.

    Used at OTP verify.

    Name policy:
    - Existing user: returned unchanged; `name` argument is ignored.
    - New user: created with the provided `name`.
    """
    user = await uow.users.get_by_email(email)
    if user is not None:
        return user
    user = User(email=email, name=name, phone=phone)
    return await uow.users.add(user)


async def update_current_user_profile(
    uow: UnitOfWork,
    user: User,
    schema: CurrentUserUpdate,
) -> User:
    """Update only frontend-editable current-user profile fields."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    return await uow.users.save(user)
