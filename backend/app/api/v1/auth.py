"""
API роутер для аутентификации.

Magic Link flow:
1. POST /auth/magic-link/request {email, name} → отправка письма
2. GET /auth/magic-link/verify?token=xxx → возврат JWT (обычно вызывается с фронта после redirect)
3. POST /auth/refresh {refresh_token} → обновление access token
"""
from fastapi import APIRouter, Depends, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_required, get_db
from app.schemas.auth import (
    MagicLinkRequest,
    MagicLinkSentResponse,
    RefreshTokenRequest,
    TokenResponse,
)
from app.models.user import User
from app.schemas.user import UserResponse
from app.services.auth import (
    refresh_access_token,
    request_magic_link,
    verify_magic_link,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/magic-link/request", response_model=MagicLinkSentResponse)
async def magic_link_request(
    schema: MagicLinkRequest,
    db: AsyncSession = Depends(get_db),
) -> MagicLinkSentResponse:
    """
    Запросить Magic Link на email.

    Создаёт пользователя при первом запросе.
    Отправляет письмо со ссылкой (или логирует в dev).
    """
    await request_magic_link(db, schema.email, schema.name)
    return MagicLinkSentResponse()


@router.get("/magic-link/verify")
async def magic_link_verify(
    token: str = Query(..., description="Токен из ссылки в письме"),
    db: AsyncSession = Depends(get_db),
):
    """
    Проверить Magic Link токен и выдать JWT.

    Вызывается когда пользователь переходит по ссылке из письма.
    Frontend обычно получает token из query и вызывает этот endpoint.
    """
    user, access_token, refresh_token = await verify_magic_link(db, token)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    schema: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Обновить access token по refresh token."""
    access_token, refresh_token = await refresh_access_token(db, schema.refresh_token)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_me(
    user: User = Depends(get_current_user_required),
) -> UserResponse:
    """
    Получить текущего пользователя по Bearer token.

    Защищённый эндпоинт — требует Authorization: Bearer <access_token>.
    """
    return user
