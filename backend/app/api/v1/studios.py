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
