"""
Pydantic schemas для User модели.

Паттерн RORO (Receive an Object, Return an Object):
- UserCreate: данные для создания пользователя
- UserUpdate: данные для обновления (все поля опциональные)
- UserResponse: данные для ответа API (включая id, timestamps)

Почему отдельные схемы:
- Безопасность: не возвращаем внутренние поля (magic_link_token)
- Валидация: разные правила для создания и обновления
- Гибкость: можем добавлять вычисляемые поля в Response
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Базовые поля пользователя (общие для Create и Update)."""
    email: EmailStr = Field(..., description="Email пользователя (уникальный)")
    name: str = Field(..., min_length=1, max_length=100, description="Имя пользователя")
    phone: str | None = Field(None, max_length=20, description="Номер телефона (опционально)")


class UserCreate(UserBase):
    """Схема для создания пользователя."""
    pass


class UserUpdate(BaseModel):
    """Схема для обновления пользователя (все поля опциональные)."""
    email: EmailStr | None = Field(None, description="Email пользователя")
    name: str | None = Field(None, min_length=1, max_length=100, description="Имя пользователя")
    phone: str | None = Field(None, max_length=20, description="Номер телефона")


class UserResponse(UserBase):
    """Схема для ответа API (включает id и timestamps)."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    class Config:
        from_attributes = True  # Pydantic v2: позволяет создавать из SQLAlchemy моделей


class UserPublic(UserBase):
    """Публичная информация о пользователе (без внутренних данных)."""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
