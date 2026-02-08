"""
Общие зависимости для API роутеров.

Почему отдельный файл deps.py:
- Централизованное управление зависимостями
- Переиспользование в разных роутерах
- Упрощение тестирования (легко мокировать)
"""
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth import get_current_user_from_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Получить текущего пользователя по Bearer token.

    Возвращает None если токен не передан или невалиден.
    Используйте для опциональной аутентификации.
    """
    if credentials is None:
        return None
    return await get_current_user_from_token(db, credentials.credentials)


async def get_current_user_required(
    user: User | None = Depends(get_current_user),
) -> User:
    """
    Получить текущего пользователя, обязательная аутентификация.

    Raises 401 если пользователь не аутентифицирован.
    """
    if user is None:
        raise HTTPException(status_code=401, detail="Требуется аутентификация")
    return user


__all__ = ["get_db", "get_current_user", "get_current_user_required"]
