from typing import Annotated

"""
API роутер для студий.

CRUD операции:
- GET /studios — список с пагинацией
- GET /studios/{id} — одна студия
- POST /studios — создать
- PATCH /studios/{id} — обновить
- DELETE /studios/{id} — удалить

Почему роутер вынесен отдельно:
- Тонкий слой: только HTTP логика, валидация, вызов сервисов
- Соответствует структуре из .cursorrules
"""

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.models.user import User
from app.modules.catalog.studio import (
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    create_studio,
    delete_studio,
    ensure_studio_owner,
    get_studio_or_raise,
    get_studios,
    get_studios_count,
    update_studio,
)
from app.modules.catalog.studio.explore import attach_services_to_studios

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("")
async def list_studios(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    owner_id: int | None = Query(None, description="Фильтр по владельцу (для панели owner)"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
    city: str | None = Query(None, description="Город (Explore)"),
    category: ServiceCategory | None = Query(None, description="Категория услуги (Explore)"),
    query: str | None = Query(None, description="Поиск по названию студии/услуги (Explore)"),
    amenities: list[str] | None = Query(None, description="Удобства (Explore)"),
    include_services: bool = Query(
        False, description="Вернуть услуги для карточек (цена, категория)"
    ),
):
    """
    Список студий с пагинацией и опциональными фильтрами для Explore.
    При include_services=true возвращает list[SearchResult] (студия + услуги), иначе list[StudioResponse].
    """
    studios = await get_studios(
        uow,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    if not include_services:
        return [StudioResponse.model_validate(s) for s in studios]

    return await attach_services_to_studios(
        uow,
        studios,
        category=category.value if category is not None else None,
    )


@router.get("/count")
async def count_studios(
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    owner_id: int | None = Query(None, description="Фильтр по владельцу"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
    city: str | None = Query(None, description="Город (Explore)"),
    category: ServiceCategory | None = Query(None, description="Категория услуги (Explore)"),
    query: str | None = Query(None, description="Поиск по названию (Explore)"),
    amenities: list[str] | None = Query(None, description="Удобства (Explore)"),
) -> dict[str, int]:
    """Количество студий (для пагинации, те же фильтры что и list)."""
    count = await get_studios_count(
        uow,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    return {"count": count}


@router.get("/{studio_id}", response_model=StudioResponse)
async def get_studio_by_id(
    studio_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """Получить студию по ID."""
    studio = await get_studio_or_raise(uow, studio_id)
    return StudioResponse.model_validate(studio)


@router.post("", response_model=StudioResponse, status_code=201)
async def create_studio_endpoint(
    schema: StudioCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """
    Создать студию (требуется аутентификация).
    owner_id берётся из токена, переданный в schema игнорируется.
    """
    schema_with_owner = schema.model_copy(update={"owner_id": user.id})
    studio = await create_studio(uow, schema_with_owner)
    return StudioResponse.model_validate(studio)


@router.patch("/{studio_id}", response_model=StudioResponse)
async def update_studio_endpoint(
    studio_id: int,
    schema: StudioUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """Обновить студию (только владелец)."""
    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)
    studio = await update_studio(uow, studio, schema)
    return StudioResponse.model_validate(studio)


@router.delete("/{studio_id}", status_code=204)
async def delete_studio_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Удалить студию (только владелец). Удалятся и связанные слоты."""
    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_studio(uow, studio)
