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

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_required, get_db
from app.models.user import User
from app.schemas import (
    SlotResponse,
    StudioCreate,
    StudioPublicResponse,
    StudioResponse,
    StudioUpdate,
)
from app.services.slot import get_slots
from app.services.studio import (
    create_studio,
    delete_studio,
    get_studio,
    get_studios,
    get_studios_count,
    update_studio,
)
from app.services.service import (
    get_studio_public,
    occurrence_generator,
)

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("", response_model=list[StudioResponse])
async def list_studios(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    owner_id: int | None = Query(None, description="Фильтр по владельцу (для панели owner)"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> list[StudioResponse]:
    """
    Список студий с пагинацией.
    """
    studios = await get_studios(
        db, skip=skip, limit=limit, owner_id=owner_id, is_active=is_active
    )
    return studios


@router.get("/count")
async def count_studios(
    db: AsyncSession = Depends(get_db),
    owner_id: int | None = Query(None, description="Фильтр по владельцу"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество студий (для пагинации)."""
    count = await get_studios_count(db, owner_id=owner_id, is_active=is_active)
    return {"count": count}


@router.get("/{studio_id}/slots", response_model=list[SlotResponse])
async def list_studio_slots(
    studio_id: int,
    db: AsyncSession = Depends(get_db),
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
        db,
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
    db: AsyncSession = Depends(get_db),
) -> StudioResponse:
    """Получить студию по ID."""
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    return studio


@router.get("/slug/{slug}/public", response_model=StudioPublicResponse)
async def get_studio_public_endpoint(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> StudioPublicResponse:
    """
    Публичное представление студии по slug.

    Возвращает список услуг и ближайшие занятия.
    """
    return await get_studio_public(db, slug=slug)


@router.post("/{studio_id}/generate-schedule", response_model=list[SlotResponse])
async def generate_studio_schedule_endpoint(
    studio_id: int,
    payload: dict,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
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
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    if studio.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой студии")

    from datetime import time as time_cls

    try:
        service_id = int(payload["service_id"])
        days = list(map(int, payload["days"]))
        start_time_str: str = payload["start_time"]
        weeks_count = int(payload["weeks_count"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(status_code=400, detail="Неверный формат payload")

    # Разбираем время в формате HH:MM[:SS]
    try:
        parts = [int(p) for p in start_time_str.split(":")]
        if len(parts) == 2:
            start_time = time_cls(parts[0], parts[1])
        elif len(parts) == 3:
            start_time = time_cls(parts[0], parts[1], parts[2])
        else:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный формат start_time")

    slots = await occurrence_generator(
        db,
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
    db: AsyncSession = Depends(get_db),
) -> StudioResponse:
    """
    Создать студию (требуется аутентификация).
    owner_id берётся из токена, переданный в schema игнорируется.
    """
    schema_with_owner = schema.model_copy(update={"owner_id": user.id})
    studio = await create_studio(db, schema_with_owner)
    return studio


@router.patch("/{studio_id}", response_model=StudioResponse)
async def update_studio_endpoint(
    studio_id: int,
    schema: StudioUpdate,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> StudioResponse:
    """Обновить студию (только владелец)."""
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    if studio.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой студии")
    return await update_studio(db, studio, schema)


@router.delete("/{studio_id}", status_code=204)
async def delete_studio_endpoint(
    studio_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить студию (только владелец). Удалятся и связанные слоты."""
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    if studio.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой студии")
    await delete_studio(db, studio)
