"""
Бизнес-логика для студий.

Почему сервисный слой:
- Роутеры остаются тонкими (только HTTP логика)
- Бизнес-логика в одном месте — проще тестировать
- Переиспользование в разных эндпоинтах (API, webhooks, CLI)
"""
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.service import Service
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
    city: str | None = None,
    category: str | None = None,
    query: str | None = None,
    amenities: list[str] | None = None,
) -> list[Studio]:
    """
    Список студий с пагинацией и фильтрами.

    skip, limit — для пагинации
    owner_id — фильтр по владельцу (для панели owner)
    is_active — фильтр по статусу (None = все)
    city — фильтр по городу (регистронезависимый)
    category — фильтр по категории услуги (join Service)
    query — поиск по названию студии или услуги (ilike)
    amenities — студия должна содержать все указанные удобства
    """
    conditions = []
    if owner_id is not None:
        conditions.append(Studio.owner_id == owner_id)
    if is_active is not None:
        conditions.append(Studio.is_active == is_active)
    if city:
        city_norm = city.strip().lower()
        if city_norm:
            conditions.append(func.lower(Studio.city) == city_norm)
    if amenities:
        for a in amenities:
            if a and a.strip():
                conditions.append(Studio.amenities.contains([a.strip()]))

    need_join = category or (query and query.strip())
    if need_join:
        join_conditions = list(conditions)
        join_conditions.append(Service.studio_id == Studio.id)
        join_conditions.append(Service.is_active.is_(True))
        if category:
            join_conditions.append(Service.category == category)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            join_conditions.append(
                or_(
                    Studio.name.ilike(pattern),
                    Service.name.ilike(pattern),
                )
            )
        subq = (
            select(Studio.id)
            .join(Service, Service.studio_id == Studio.id)
            .where(and_(*join_conditions))
            .distinct()
        )
        stmt = (
            select(Studio)
            .where(Studio.id.in_(subq))
            .order_by(Studio.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
    else:
        stmt = select(Studio)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(Studio.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_studios_count(
    db: AsyncSession,
    *,
    owner_id: int | None = None,
    is_active: bool | None = None,
    city: str | None = None,
    category: str | None = None,
    query: str | None = None,
    amenities: list[str] | None = None,
) -> int:
    """Подсчёт студий для пагинации (те же фильтры, что и get_studios)."""
    conditions = []
    if owner_id is not None:
        conditions.append(Studio.owner_id == owner_id)
    if is_active is not None:
        conditions.append(Studio.is_active == is_active)
    if city:
        city_norm = city.strip().lower()
        if city_norm:
            conditions.append(func.lower(Studio.city) == city_norm)
    if amenities:
        for a in amenities:
            if a and a.strip():
                conditions.append(Studio.amenities.contains([a.strip()]))

    need_join = category or (query and query.strip())
    if need_join:
        join_conditions = list(conditions)
        join_conditions.append(Service.studio_id == Studio.id)
        join_conditions.append(Service.is_active.is_(True))
        if category:
            join_conditions.append(Service.category == category)
        if query and query.strip():
            pattern = f"%{query.strip()}%"
            join_conditions.append(
                or_(
                    Studio.name.ilike(pattern),
                    Service.name.ilike(pattern),
                )
            )
        subq = (
            select(Studio.id)
            .join(Service, Service.studio_id == Studio.id)
            .where(and_(*join_conditions))
            .distinct()
        )
        stmt = select(func.count()).select_from(subq.subquery())
    else:
        stmt = select(func.count()).select_from(Studio)
        if conditions:
            stmt = stmt.where(*conditions)
    result = await db.execute(stmt)
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
