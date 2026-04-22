"""
Authentication business logic: magic link and JWT.
"""

from datetime import UTC, datetime

from app.core.config import settings
from app.core.exceptions import UnauthorizedError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_csrf_token,
    generate_magic_link_token,
    get_magic_link_expires_at,
    get_user_id_from_access_token,
    hash_magic_link_token,
    parse_refresh_token,
)
from app.core.uow import UnitOfWork
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.email import send_magic_link_email
from app.services.user import get_or_create_user, get_user_by_id


async def request_magic_link(
    uow: UnitOfWork,
    email: str,
    name: str,
) -> None:
    """
    Request a magic link.

    1. Creates or updates user by email/name
    2. Generates token and stores hash in DB
    3. Sends email with link
    """
    user = await get_or_create_user(uow, email=email, name=name)
    token = generate_magic_link_token()
    user.magic_link_token = hash_magic_link_token(token)
    user.magic_link_expires_at = get_magic_link_expires_at()
    await uow.session.flush()

    magic_link_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
    await send_magic_link_email(email, magic_link_url)


async def verify_magic_link(
    uow: UnitOfWork,
    token: str,
) -> tuple[User, str, str, str]:
    """
    Verify magic link token.

    Returns (user, access_token, refresh_token, csrf_token).
    Raises ValidationError if the token is invalid.
    """
    now_utc = datetime.now(UTC)
    token_hash = hash_magic_link_token(token)
    user = await uow.users.get_by_magic_link_token(token_hash, now_utc)
    if user is None:
        raise ValidationError("Magic link is invalid or has expired")

    user.magic_link_token = None
    user.magic_link_expires_at = None
    user.last_login_at = now_utc
    await uow.session.flush()
    await uow.session.refresh(user)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    csrf_token = create_csrf_token()

    refresh_data = parse_refresh_token(refresh_token)
    if refresh_data is not None:
        uow.session.add(
            RefreshToken(
                user_id=user.id,
                jti=refresh_data.jti,
                expires_at=refresh_data.expires_at,
            )
        )
        await uow.session.flush()

    return user, access_token, refresh_token, csrf_token


async def refresh_access_token(
    uow: UnitOfWork,
    refresh_token: str,
) -> tuple[str, str, str]:
    """
    Issue new access token from refresh token.

    Returns (access_token, refresh_token, csrf_token).
    Raises UnauthorizedError if refresh token is invalid.
    """
    refresh_data = parse_refresh_token(refresh_token)
    if refresh_data is None:
        raise UnauthorizedError("Invalid refresh token")

    user_id = refresh_data.user_id
    jti = refresh_data.jti
    now_utc = datetime.now(UTC)

    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user_id, jti)
    if refresh_session is None or not refresh_session.is_active(now_utc):
        raise UnauthorizedError("Invalid refresh token")

    refresh_session.revoked_at = now_utc
    refresh_session.last_used_at = now_utc

    user = await get_user_by_id(uow, user_id)
    if user is None:
        raise UnauthorizedError("User not found")

    access_token = create_access_token(user.id, user.email)
    new_refresh_token = create_refresh_token(user.id)
    new_csrf_token = create_csrf_token()

    new_data = parse_refresh_token(new_refresh_token)
    if new_data is not None:
        uow.session.add(
            RefreshToken(
                user_id=user.id,
                jti=new_data.jti,
                expires_at=new_data.expires_at,
            )
        )

    await uow.session.flush()
    return access_token, new_refresh_token, new_csrf_token


async def get_current_user_from_token(
    uow: UnitOfWork,
    token: str,
) -> User | None:
    """Resolve user from access token."""
    user_id = get_user_id_from_access_token(token)
    if user_id is None:
        return None
    return await get_user_by_id(uow, user_id)


async def logout_current_session(
    uow: UnitOfWork,
    user: User,
    refresh_token: str,
) -> None:
    """
    Sign out of current session (revoke one refresh token).

    If token is invalid or not owned by user — silent no-op (idempotent).
    If session exists and active — sets revoked_at / last_used_at.
    """
    data = parse_refresh_token(refresh_token)
    if data is None or data.user_id != user.id:
        return

    now_utc = datetime.now(UTC)
    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user.id, data.jti)
    if refresh_session is None:
        return

    if refresh_session.revoked_at is None:
        refresh_session.revoked_at = now_utc
        refresh_session.last_used_at = now_utc
        await uow.session.flush()
