"""JWT session refresh, resolution, and logout."""

import structlog

from app.core.datetime_utils import utc_now
from app.core.exceptions import UnauthorizedError
from app.core.observability import log_domain_event
from app.core.security import (
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    get_user_id_from_access_token,
    parse_refresh_token,
)
from app.core.uow import UnitOfWork
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.modules.identity import get_user_by_id

logger = structlog.get_logger(__name__)


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
    now_utc = utc_now()

    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user_id, jti)
    if refresh_session is None:
        raise UnauthorizedError("Invalid refresh token")
    if refresh_session.revoked_at is not None:
        revoked_count = await uow.refresh_tokens.revoke_active_for_user(user_id, now_utc)
        log_domain_event(
            logger,
            "refresh_token_reuse_detected",
            level="warning",
            user_id=user_id,
            revoked_sessions=revoked_count,
        )
        # WHY: this security side effect must survive the 401 response rollback path.
        await uow.commit()
        raise UnauthorizedError("Invalid refresh token")
    if not refresh_session.is_active(now_utc):
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
        await uow.refresh_tokens.add(
            RefreshToken(
                user_id=user.id,
                jti=new_data.jti,
                expires_at=new_data.expires_at,
            )
        )

    await uow.refresh_tokens.flush()
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

    now_utc = utc_now()
    refresh_session = await uow.refresh_tokens.get_by_user_and_jti(user.id, data.jti)
    if refresh_session is None:
        return

    if refresh_session.revoked_at is None:
        refresh_session.revoked_at = now_utc
        refresh_session.last_used_at = now_utc
        await uow.refresh_tokens.save(refresh_session)
