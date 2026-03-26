"""
Shared dependencies for API routers.

Centralized DI, reuse across routers, easier testing (mock get_uow).

`get_db` is exported for possible read-only endpoints without UoW;
routers default to `get_uow`.
"""

from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import Request

from app.core.database import async_session_maker, get_db
from app.core.exceptions import UnauthorizedError
from app.core.middleware.logging_middleware import USER_ID_STATE_KEY
from app.core.uow import UnitOfWork, create_uow
from app.models.user import User
from app.services.auth import get_current_user_from_token

security = HTTPBearer(auto_error=False)


async def get_uow() -> AsyncGenerator[UnitOfWork]:
    """
    Unit of Work with transaction management for write paths.

    Creates AsyncSession, wraps UnitOfWork with repositories, commits on success
    and rolls back on error.
    """
    async with async_session_maker() as session:
        uow = create_uow(session)
        try:
            yield uow
            await uow.commit()
        except Exception:
            await uow.rollback()
            raise


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    uow: UnitOfWork = Depends(get_uow),
) -> User | None:
    """
    Resolve current user from Bearer token.

    Returns None if no token or invalid token (optional auth).
    Sets request.state.user_id for logging middleware when user is found.
    """
    if credentials is None:
        return None
    user = await get_current_user_from_token(uow, credentials.credentials)
    if user is not None:
        setattr(request.state, USER_ID_STATE_KEY, str(user.id))
    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    Require authenticated user.

    Raises 401 if not authenticated.
    """
    if user is None:
        raise UnauthorizedError("Authentication required")
    return user


__all__ = ["get_db", "get_current_user", "get_current_user_required", "get_uow"]
