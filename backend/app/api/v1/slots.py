"""
API роутер для слотов (расписание).

CRUD операции:
- GET /slots — список с фильтрами (расписание)
- GET /slots/{id} — один слот
- POST /slots — создать
- PATCH /slots/{id} — обновить
- DELETE /slots/{id} — удалить

Вложенные маршруты:
- GET /studios/{studio_id}/slots — расписание конкретной студии
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.schemas.booking import BookingResponse
from app.schemas.slot import SlotCreate, SlotResponse, SlotUpdate
from app.services.booking import get_bookings
from app.services.slot import (
    create_slot,
    delete_slot,
    get_slot_or_raise,
    get_slots,
    get_slots_count,
    update_slot,
)
from app.services.studio import ensure_studio_owner, get_studio_or_raise

router = APIRouter(prefix="/slots", tags=["slots"])


@router.get("", response_model=list[SlotResponse])
async def list_slots(
    uow: UnitOfWork = Depends(get_uow),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    studio_id: int | None = Query(None, description="Фильтр по студии"),
    start_from: datetime | None = Query(None, description="Начало диапазона дат"),
    start_to: datetime | None = Query(None, description="Конец диапазона дат"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> list[SlotResponse]:
    """
    Список слотов с фильтрами.

    Для расписания студии: studio_id + start_from/start_to.
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


@router.get("/count")
async def count_slots(
    uow: UnitOfWork = Depends(get_uow),
    studio_id: int | None = Query(None, description="Фильтр по студии"),
    start_from: datetime | None = Query(None, description="Начало диапазона дат"),
    start_to: datetime | None = Query(None, description="Конец диапазона дат"),
    is_active: bool | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество слотов (для пагинации)."""
    count = await get_slots_count(
        uow,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        is_active=is_active,
    )
    return {"count": count}


@router.get("/{slot_id}/bookings", response_model=list[BookingResponse])
async def list_slot_bookings(
    slot_id: int,
    uow: UnitOfWork = Depends(get_uow),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> list[BookingResponse]:
    """Бронирования слота."""
    await get_slot_or_raise(uow, slot_id)
    return await get_bookings(uow, skip=skip, limit=limit, slot_id=slot_id, status=status)


@router.get("/{slot_id}", response_model=SlotResponse)
async def get_slot_by_id(
    slot_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> SlotResponse:
    """Получить слот по ID."""
    return await get_slot_or_raise(uow, slot_id)


@router.post("", response_model=SlotResponse, status_code=201)
async def create_slot_endpoint(
    schema: SlotCreate,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> SlotResponse:
    """
    Создать слот (требуется аутентификация, владелец студии).
    """
    studio = await get_studio_or_raise(uow, schema.studio_id)
    ensure_studio_owner(studio, user.id)
    return await create_slot(uow, schema)


@router.patch("/{slot_id}", response_model=SlotResponse)
async def update_slot_endpoint(
    slot_id: int,
    schema: SlotUpdate,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> SlotResponse:
    """Обновить слот (только владелец студии)."""
    slot = await get_slot_or_raise(uow, slot_id)
    studio = await get_studio_or_raise(uow, slot.studio_id)
    ensure_studio_owner(studio, user.id)
    return await update_slot(uow, slot, schema)


@router.delete("/{slot_id}", status_code=204)
async def delete_slot_endpoint(
    slot_id: int,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Удалить слот (только владелец студии). Удалятся и связанные бронирования."""
    slot = await get_slot_or_raise(uow, slot_id)
    studio = await get_studio_or_raise(uow, slot.studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_slot(uow, slot)
