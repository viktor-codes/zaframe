"""
Бизнес-логика для пользователей.
"""

import structlog

from app.core import datetime_utils
from app.core.exceptions import UnauthorizedError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.identity.schemas import CurrentUserUpdate

logger = structlog.get_logger(__name__)


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
    user = await uow.users.get_by_email_including_deleted(email)
    if user is not None:
        if user.deleted_at is not None:
            raise UnauthorizedError("Account is deleted")
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
    if "name" in update_data:
        user.name = update_data["name"]
    if "phone" in update_data:
        user.phone = update_data["phone"]
    if "marketing_consent" in update_data:
        user.marketing_consent = update_data["marketing_consent"]
    updated_user = await uow.users.save(user)
    log_domain_event(
        logger,
        "user_profile_updated",
        user_id=updated_user.id,
        updated_fields=sorted(update_data.keys()),
    )
    return updated_user


async def soft_delete_current_user_account(uow: UnitOfWork, user: User) -> User:
    """Soft-delete current user and revoke all active refresh-token sessions."""
    now_utc = datetime_utils.utc_now()
    if user.deleted_at is None:
        user.deleted_at = now_utc
    await uow.refresh_tokens.revoke_active_for_user(user.id, now_utc)
    deleted_user = await uow.users.save(user)
    log_domain_event(logger, "user_account_soft_deleted", user_id=deleted_user.id)
    return deleted_user
