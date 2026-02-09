"""
Бизнес-логика аутентификации: Magic Link, JWT.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_magic_link_token,
    get_magic_link_expires_at,
    get_user_id_from_access_token,
    get_user_id_from_refresh_token,
)
from app.models.user import User
from app.services.email import send_magic_link_email
from app.services.user import get_or_create_user, get_user_by_id


async def request_magic_link(
    db: AsyncSession,
    email: str,
    name: str,
) -> None:
    """
    Запросить Magic Link.

    1. Создаёт пользователя по email/name или обновляет существующего
    2. Генерирует токен, сохраняет в БД
    3. Отправляет email и ссылкой
    """
    user = await get_or_create_user(db, email=email, name=name)
    token = generate_magic_link_token()
    user.magic_link_token = token
    user.magic_link_expires_at = get_magic_link_expires_at()
    await db.flush()

    magic_link_url = f"{settings.FRONTEND_URL}/auth/verify?token={token}"
    await send_magic_link_email(email, magic_link_url)


async def verify_magic_link(
    db: AsyncSession,
    token: str,
) -> tuple[User, str, str]:
    """
    Проверить Magic Link токен.

    Возвращает (user, access_token, refresh_token).
    Raises HTTPException если токен невалиден.
    """
    # Используем naive datetime для сравнения с БД (TIMESTAMP WITHOUT TIME ZONE)
    now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
    result = await db.execute(
        select(User).where(
            User.magic_link_token == token,
            User.magic_link_expires_at > now_naive,
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=400, detail="Ссылка недействительна или истекла")

    user.magic_link_token = None
    user.magic_link_expires_at = None
    # Преобразуем в naive datetime для БД (TIMESTAMP WITHOUT TIME ZONE)
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    await db.flush()

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id)
    return user, access_token, refresh_token


async def refresh_access_token(
    db: AsyncSession,
    refresh_token: str,
) -> tuple[str, str]:
    """
    Обновить access token по refresh token.

    Возвращает (access_token, refresh_token).
    Raises HTTPException если refresh token невалиден.
    """
    user_id = get_user_id_from_refresh_token(refresh_token)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Недействительный refresh token")

    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Пользователь не найден")

    return create_access_token(user.id, user.email), create_refresh_token(user.id)


async def get_current_user_from_token(
    db: AsyncSession,
    token: str,
) -> User | None:
    """Получить пользователя по access token."""
    user_id = get_user_id_from_access_token(token)
    if user_id is None:
        return None
    return await get_user_by_id(db, user_id)
