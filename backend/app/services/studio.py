"""
Бизнес-логика для студий.

Почему сервисный слой:
- Роутеры остаются тонкими (только HTTP логика)
- Бизнес-логика в одном месте — проще тестировать
- Переиспользование в разных эндпоинтах (API, webhooks, CLI)
"""
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.schemas.studio import StudioCreate, StudioUpdate


async def get_studio(uow: UnitOfWork, studio_id: int) -> Studio | None:
    """Получить студию по ID. Возвращает None если не найдена."""
    return await uow.studios.get_by_id(studio_id)


async def get_studios(
    uow: UnitOfWork,
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
    """Список студий с пагинацией и фильтрами."""
    return await uow.studios.list_(
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category,
        query=query,
        amenities=amenities,
    )


async def get_studios_count(
    uow: UnitOfWork,
    *,
    owner_id: int | None = None,
    is_active: bool | None = None,
    city: str | None = None,
    category: str | None = None,
    query: str | None = None,
    amenities: list[str] | None = None,
) -> int:
    """Подсчёт студий для пагинации (те же фильтры, что и get_studios)."""
    return await uow.studios.count(
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category,
        query=query,
        amenities=amenities,
    )


async def get_studio_or_raise(uow: UnitOfWork, studio_id: int) -> Studio:
    """Получить студию по ID или выбросить NotFoundError."""
    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Студия не найдена")
    return studio


def ensure_studio_owner(studio: Studio, user_id: int) -> None:
    """Проверить, что user_id — владелец студии; иначе ForbiddenError."""
    if studio.owner_id != user_id:
        raise ForbiddenError("Нет доступа к этой студии")


async def create_studio(uow: UnitOfWork, schema: StudioCreate) -> Studio:
    """Создать студию. owner_id должен быть передан в schema (из токена на уровне роутера)."""
    if schema.owner_id is None:
        raise ValidationError("Владелец не указан или не найден")
    owner = await uow.users.get_by_id(schema.owner_id)
    if owner is None:
        raise ValidationError("Владелец не указан или не найден")

    studio = Studio(
        owner_id=schema.owner_id,
        name=schema.name,
        description=schema.description,
        email=schema.email,
        phone=schema.phone,
        address=schema.address,
    )
    uow.session.add(studio)
    await uow.session.flush()
    await uow.session.refresh(studio)
    return studio


async def update_studio(
    uow: UnitOfWork,
    studio: Studio,
    schema: StudioUpdate,
) -> Studio:
    """Обновить студию (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(studio, field, value)
    await uow.session.flush()
    await uow.session.refresh(studio)
    return studio


async def delete_studio(uow: UnitOfWork, studio: Studio) -> None:
    """Удалить студию. Cascade удалит связанные слоты."""
    await uow.session.delete(studio)
    await uow.session.flush()
