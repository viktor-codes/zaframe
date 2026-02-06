"""
Pydantic schemas для GuestSession модели.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class GuestSessionBase(BaseModel):
    """Базовые поля гостевой сессии."""
    email: EmailStr = Field(..., description="Email гостя")
    name: str = Field(..., min_length=1, max_length=100, description="Имя гостя")
    phone: str | None = Field(None, max_length=20, description="Телефон гостя (опционально)")


class GuestSessionCreate(GuestSessionBase):
    """Схема для создания гостевой сессии."""
    pass


class GuestSessionResponse(GuestSessionBase):
    """Схема для ответа API."""
    id: int
    session_id: str
    expires_at: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
