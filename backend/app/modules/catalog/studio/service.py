"""
Бизнес-логика для студий.

Почему сервисный слой:
- Роутеры остаются тонкими (только HTTP логика)
- Бизнес-логика в одном месте — проще тестировать
- Переиспользование в разных эндпоинтах (API, webhooks, CLI)
"""

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.studio import Studio
from app.modules.catalog.studio.schemas import StudioCreate, StudioUpdate


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


async def get_my_studios(uow: UnitOfWork, *, owner_id: int) -> list[Studio]:
    """List studios owned by the current user."""
    return await uow.studios.list_(owner_id=owner_id, limit=100)


async def get_studio_or_raise(uow: UnitOfWork, studio_id: int) -> Studio:
    """Получить студию по ID или выбросить NotFoundError."""
    studio = await uow.studios.get_by_id(studio_id)
    if studio is None:
        raise NotFoundError("Studio not found")
    return studio


def ensure_studio_owner(studio: Studio, user_id: int) -> None:
    """Проверить, что user_id — владелец студии; иначе ForbiddenError."""
    if studio.owner_id != user_id:
        raise ForbiddenError("Access denied for this studio")


async def ensure_studio_slug_available(
    uow: UnitOfWork,
    *,
    slug: str | None,
    current_studio_id: int | None = None,
) -> None:
    """Validate slug uniqueness across studios."""
    if slug is None:
        return
    existing = await uow.studios.get_by_slug(slug)
    if existing is not None and existing.id != current_studio_id:
        raise ConflictError("Studio slug is already in use")


async def create_studio(uow: UnitOfWork, schema: StudioCreate) -> Studio:
    """Создать студию. owner_id должен быть передан в schema (из токена на уровне роутера)."""
    if schema.owner_id is None:
        raise ValidationError("Owner is missing or not found")
    owner = await uow.users.get_by_id(schema.owner_id)
    if owner is None:
        raise ValidationError("Owner is missing or not found")
    await ensure_studio_slug_available(uow, slug=schema.slug)

    studio = Studio(
        owner_id=schema.owner_id,
        name=schema.name,
        slug=schema.slug,
        description=schema.description,
        logo_url=schema.logo_url,
        cover_url=schema.cover_url,
        email=schema.email,
        phone=schema.phone,
        address=schema.address,
        city=schema.city,
        latitude=schema.latitude,
        longitude=schema.longitude,
        amenities=schema.amenities,
        timezone=schema.timezone,
    )
    return await uow.studios.add(studio)


async def update_studio(
    uow: UnitOfWork,
    studio: Studio,
    schema: StudioUpdate,
) -> Studio:
    """Обновить студию (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    if "timezone" in update_data and update_data["timezone"] != studio.timezone:
        occurrence_count = await uow.occurrences.count(studio_id=studio.id)
        if occurrence_count > 0:
            raise ValidationError("Cannot change timezone after occurrences have been created")
    if "slug" in update_data:
        await ensure_studio_slug_available(
            uow,
            slug=update_data["slug"],
            current_studio_id=studio.id,
        )
    for field, value in update_data.items():
        setattr(studio, field, value)
    return await uow.studios.save(studio)


async def delete_studio(uow: UnitOfWork, studio: Studio) -> None:
    """Delete studio. Cascades to related occurrences."""
    await uow.studios.delete(studio)
