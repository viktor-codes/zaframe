"""
Shared FastAPI dependencies (DI).

Routers depend on this module — not on app.api — so import-linter can keep the API
layer at the top. User resolution uses core.security + identity (not auth).
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.requests import Request

from app.core.exceptions import UnauthorizedError
from app.core.middleware.logging_middleware import USER_ID_STATE_KEY
from app.core.security import get_user_id_from_access_token
from app.core.uow import UnitOfWork
from app.core.uow_factory import get_uow
from app.models.user import User
from app.modules.identity import get_user_by_id

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> User | None:
    """
    Resolve current user from Bearer token.

    Returns None if no token or invalid token (optional auth).
    Sets request.state.user_id for logging middleware when user is found.
    """
    if credentials is None:
        return None
    user_id = get_user_id_from_access_token(credentials.credentials)
    if user_id is None:
        return None
    user = await get_user_by_id(uow, user_id)
    if user is not None:
        setattr(request.state, USER_ID_STATE_KEY, str(user.id))
    return user


async def get_current_user_required(
    user: Annotated[User | None, Depends(get_current_user)],
) -> User:
    """
    Require authenticated user.

    Raises 401 if not authenticated.
    """
    if user is None:
        raise UnauthorizedError("Authentication required")
    return user


__all__ = ["get_current_user", "get_current_user_required", "get_uow"]
