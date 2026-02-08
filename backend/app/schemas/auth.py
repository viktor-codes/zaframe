"""
Pydantic schemas для аутентификации.
"""
from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """Запрос Magic Link на email."""
    email: EmailStr = Field(..., description="Email для входа")
    name: str = Field(..., min_length=1, max_length=100, description="Имя (для регистрации)")


class TokenResponse(BaseModel):
    """Ответ с JWT токенами."""
    access_token: str = Field(..., description="Access token для API")
    refresh_token: str = Field(..., description="Refresh token для обновления")
    token_type: str = Field(default="bearer", description="Тип токена")


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена."""
    refresh_token: str = Field(..., description="Refresh token")


class MagicLinkSentResponse(BaseModel):
    """Ответ после отправки Magic Link."""
    message: str = Field(
        default="Если email зарегистрирован, вы получите ссылку для входа",
        description="Сообщение пользователю"
    )
