"""
Бизнес-логика для студий.

Почему сервисный слой:
- Роутеры остаются тонкими (только HTTP логика)
- Бизнес-логика в одном месте — проще тестировать
- Переиспользование в разных эндпоинтах (API, webhooks, CLI)
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.studio import Studio
from app.schemas.studio import StudioCreate, StudioUpdate


async def get_studio(db: AsyncSession, studio_id: int) -> Studio | None:
    """
    Получить студию по ID.
    
    Возвращает None если студия не найдена.
    """
    result = await db.execute(select(Studio).where(Studio.id == studio_id))
    return result.scalar_one_or_none()


async def get_studios(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    owner_id: int | None = None,
    is_active: bool | None = None,
) -> list[Studio]:
    """
    Список студий с пагинацией.

    skip, limit — для пагинации
    owner_id — фильтр по владельцу (для панели owner)
    is_active — фильтр по статусу (None = все)
    """
    query = select(Studio)
    if owner_id is not None:
        query = query.where(Studio.owner_id == owner_id)
    if is_active is not None:
        query = query.where(Studio.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(Studio.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_studios_count(
    db: AsyncSession,
    *,
    owner_id: int | None = None,
    is_active: bool | None = None,
) -> int:
    """Подсчёт студий для пагинации."""
    query = select(func.count()).select_from(Studio)
    if owner_id is not None:
        query = query.where(Studio.owner_id == owner_id)
    if is_active is not None:
        query = query.where(Studio.is_active == is_active)
    result = await db.execute(query)
    return result.scalar_one_or_none() or 0


async def create_studio(db: AsyncSession, schema: StudioCreate) -> Studio:
    """
    Создать студию.
    owner_id должен быть передан в schema (из токена на уровне роутера).
    """
    from app.models.user import User

    # Проверка существования владельца
    result = await db.execute(select(User).where(User.id == schema.owner_id))
    if schema.owner_id is None or result.scalar_one_or_none() is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Владелец не указан или не найден")

    studio = Studio(
        owner_id=schema.owner_id,
        name=schema.name,
        description=schema.description,
        email=schema.email,
        phone=schema.phone,
        address=schema.address,
    )
    db.add(studio)
    await db.flush()  # Получаем id до commit
    await db.refresh(studio)  # Обновляем объект из БД
    return studio


async def update_studio(
    db: AsyncSession,
    studio: Studio,
    schema: StudioUpdate,
) -> Studio:
    """
    Обновить студию.
    
    Обновляет только переданные поля (partial update).
    """
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(studio, field, value)
    await db.flush()
    await db.refresh(studio)
    return studio


async def delete_studio(db: AsyncSession, studio: Studio) -> None:
    """Удалить студию. Cascade удалит связанные слоты."""
    await db.delete(studio)
    await db.flush()
