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

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_required, get_uow
from app.core.exceptions import ValidationError
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.models.user import User
from app.schemas import (
    SearchResult,
    ServiceResponse,
    SlotResponse,
    StudioCreate,
    StudioPublicResponse,
    StudioResponse,
    StudioUpdate,
)
from app.services.service import (
    get_studio_public,
    occurrence_generator,
)
from app.services.slot import get_slots
from app.services.studio import (
    create_studio,
    delete_studio,
    ensure_studio_owner,
    get_studio_or_raise,
    get_studios,
    get_studios_count,
    update_studio,
)

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("")
async def list_studios(
    uow: UnitOfWork = Depends(get_uow),
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

    studio_ids = [s.id for s in studios]
    services = await uow.services.list_active_by_studio_ids(
        studio_ids,
        category=category.value if category is not None else None,
    )
    by_studio: dict[int, list] = {}
    for svc in services:
        by_studio.setdefault(svc.studio_id, []).append(ServiceResponse.model_validate(svc))

    return [
        SearchResult(
            studio=StudioResponse.model_validate(s),
            matched_services=by_studio.get(s.id, []),
        )
        for s in studios
    ]


@router.get("/count")
async def count_studios(
    uow: UnitOfWork = Depends(get_uow),
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


@router.get("/{studio_id}/slots", response_model=list[SlotResponse])
async def list_studio_slots(
    studio_id: int,
    uow: UnitOfWork = Depends(get_uow),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    start_from: datetime | None = Query(None, description="Начало диапазона дат"),
    start_to: datetime | None = Query(None, description="Конец диапазона дат"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> list[SlotResponse]:
    """
    Расписание студии: слоты с фильтрами по датам.
    """
    slots = await get_slots(
        uow,
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        is_active=is_active,
    )
    return slots


@router.get("/{studio_id}", response_model=StudioResponse)
async def get_studio_by_id(
    studio_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> StudioResponse:
    """Получить студию по ID."""
    return await get_studio_or_raise(uow, studio_id)


@router.get("/slug/{slug}/public", response_model=StudioPublicResponse)
async def get_studio_public_endpoint(
    slug: str,
    uow: UnitOfWork = Depends(get_uow),
) -> StudioPublicResponse:
    """
    Публичное представление студии по slug.

    Возвращает список услуг и ближайшие занятия.
    """
    return await get_studio_public(uow, slug=slug)


@router.post("/{studio_id}/generate-schedule", response_model=list[SlotResponse])
async def generate_studio_schedule_endpoint(
    studio_id: int,
    payload: dict,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> list[SlotResponse]:
    """
    Сгенерировать расписание для услуги в студии.

    Payload:
    {
        "service_id": int,
        "days": [1, 3],
        "start_time": "18:00:00",
        "weeks_count": 6
    }
    """
    from datetime import time as time_cls

    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)

    try:
        service_id = int(payload["service_id"])
        days = list(map(int, payload["days"]))
        start_time_str: str = payload["start_time"]
        weeks_count = int(payload["weeks_count"])
    except (KeyError, ValueError, TypeError):
        raise ValidationError("Invalid payload format") from None

    try:
        parts = [int(p) for p in start_time_str.split(":")]
        if len(parts) == 2:
            start_time = time_cls(parts[0], parts[1])
        elif len(parts) == 3:
            start_time = time_cls(parts[0], parts[1], parts[2])
        else:
            raise ValueError
    except ValueError:
        raise ValidationError("Invalid start_time format") from None

    slots = await occurrence_generator(
        uow,
        studio_id=studio_id,
        service_id=service_id,
        days=days,
        start_time=start_time,
        weeks_count=weeks_count,
    )
    # Маппим ORM → схемы
    from app.schemas.slot import SlotResponse as SlotResponseSchema  # локальный импорт

    return [SlotResponseSchema.model_validate(s) for s in slots]


@router.post("", response_model=StudioResponse, status_code=201)
async def create_studio_endpoint(
    schema: StudioCreate,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> StudioResponse:
    """
    Создать студию (требуется аутентификация).
    owner_id берётся из токена, переданный в schema игнорируется.
    """
    schema_with_owner = schema.model_copy(update={"owner_id": user.id})
    studio = await create_studio(uow, schema_with_owner)
    return studio


@router.patch("/{studio_id}", response_model=StudioResponse)
async def update_studio_endpoint(
    studio_id: int,
    schema: StudioUpdate,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> StudioResponse:
    """Обновить студию (только владелец)."""
    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)
    return await update_studio(uow, studio, schema)


@router.delete("/{studio_id}", status_code=204)
async def delete_studio_endpoint(
    studio_id: int,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Удалить студию (только владелец). Удалятся и связанные слоты."""
    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_studio(uow, studio)
