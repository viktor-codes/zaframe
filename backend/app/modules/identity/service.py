"""Business logic for users."""

import structlog

from app.core import datetime_utils
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.identity.schemas import CurrentUserUpdate

logger = structlog.get_logger(__name__)
_DELETED_EMAIL_DOMAIN = "deleted.local"


def _anonymize_deleted_user_pii(user: User) -> None:
    """Release user-identifying fields while keeping historical relations intact."""
    user.email = f"deleted+{user.id}@{_DELETED_EMAIL_DOMAIN}"
    user.name = None
    user.phone = None


async def get_user_by_id(uow: UnitOfWork, user_id: int) -> User | None:
    """Get a user by ID."""
    return await uow.users.get_by_id(user_id)


async def get_user_by_email(uow: UnitOfWork, email: str) -> User | None:
    """Get a user by email."""
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
            _anonymize_deleted_user_pii(user)
            await uow.users.save(user)
        else:
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
    original_email = user.email
    if user.deleted_at is None:
        user.deleted_at = now_utc
        await uow.otp_codes.invalidate_active_for_email(original_email, now_utc)
        _anonymize_deleted_user_pii(user)
    await uow.refresh_tokens.revoke_active_for_user(user.id, now_utc)
    deleted_user = await uow.users.save(user)
    log_domain_event(logger, "user_account_soft_deleted", user_id=deleted_user.id)
    return deleted_user
