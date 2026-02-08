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

from app.api.deps import get_db
from app.schemas.slot import SlotResponse
from app.schemas.studio import StudioCreate, StudioResponse, StudioUpdate
from app.services.slot import get_slots
from app.services.studio import (
    create_studio,
    delete_studio,
    get_studio,
    get_studios,
    get_studios_count,
    update_studio,
)

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("", response_model=list[StudioResponse])
async def list_studios(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> list[StudioResponse]:
    """
    Список студий с пагинацией.
    """
    studios = await get_studios(db, skip=skip, limit=limit, is_active=is_active)
    return studios


@router.get("/count")
async def count_studios(
    db: AsyncSession = Depends(get_db),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество студий (для пагинации)."""
    count = await get_studios_count(db, is_active=is_active)
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


@router.post("", response_model=StudioResponse, status_code=201)
async def create_studio_endpoint(
    schema: StudioCreate,
    db: AsyncSession = Depends(get_db),
) -> StudioResponse:
    """
    Создать студию.
    
    Требуется существующий владелец (owner_id).
    После добавления аутентификации owner_id будет браться из токена.
    """
    studio = await create_studio(db, schema)
    return studio


@router.patch("/{studio_id}", response_model=StudioResponse)
async def update_studio_endpoint(
    studio_id: int,
    schema: StudioUpdate,
    db: AsyncSession = Depends(get_db),
) -> StudioResponse:
    """Обновить студию (частичное обновление)."""
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    return await update_studio(db, studio, schema)


@router.delete("/{studio_id}", status_code=204)
async def delete_studio_endpoint(
    studio_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить студию. Удалятся и связанные слоты."""
    studio = await get_studio(db, studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    await delete_studio(db, studio)
