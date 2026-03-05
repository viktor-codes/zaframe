"""
Общие зависимости для API роутеров.

Почему отдельный файл deps.py:
- Централизованное управление зависимостями
- Переиспользование в разных роутерах
- Упрощение тестирования (легко мокировать)
"""
from collections.abc import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from starlette.requests import Request

from app.core.database import async_session_maker, get_db
from app.core.exceptions import UnauthorizedError
from app.core.middleware.logging_middleware import USER_ID_STATE_KEY
from app.core.uow import UnitOfWork
from app.models.user import User
from app.services.auth import get_current_user_from_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Получить текущего пользователя по Bearer token.

    Возвращает None если токен не передан или невалиден.
    Используйте для опциональной аутентификации.
    Устанавливает request.state.user_id для логирования в middleware.
    """
    if credentials is None:
        return None
    user = await get_current_user_from_token(db, credentials.credentials)
    if user is not None:
        setattr(request.state, USER_ID_STATE_KEY, str(user.id))
    return user


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    Получить текущего пользователя, обязательная аутентификация.

    Raises 401 если пользователь не аутентифицирован.
    """
    if user is None:
        raise UnauthorizedError("Требуется аутентификация")
    return user


async def get_uow() -> AsyncGenerator[UnitOfWork, None]:
    """
    Unit of Work с управлением транзакцией для write-сценариев.

    - создаём AsyncSession
    - оборачиваем его в UnitOfWork
    - при успехе коммитим, при ошибке откатываем.
    """
    async with async_session_maker() as session:
        uow = UnitOfWork(session=session)
        try:
            yield uow
            await uow.commit()
        except Exception:
            await uow.rollback()
            raise


__all__ = ["get_db", "get_current_user", "get_current_user_required", "get_uow"]

