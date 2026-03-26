"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr, Field


class MagicLinkRequest(BaseModel):
    """Magic link request payload."""

    email: EmailStr = Field(..., description="Email для входа")
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Имя (для регистрации)",
    )


class TokenResponse(BaseModel):
    """Access token response.

    Refresh token is stored in an httpOnly cookie (strict mode) and is not
    returned in the JSON body.
    """

    access_token: str = Field(..., description="Access token для API")
    token_type: str = Field(default="bearer", description="Тип токена")


class MagicLinkSentResponse(BaseModel):
    """Response after requesting a magic link."""

    message: str = Field(
        default="Если email зарегистрирован, вы получите ссылку для входа",
        description="Сообщение пользователю",
    )
