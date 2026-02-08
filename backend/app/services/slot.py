"""
Бизнес-логика для слотов (расписание).

Почему сервисный слой:
- Роутеры остаются тонкими
- Валидация (end_time > start_time) в одном месте
- Переиспользование при бронировании
"""
from datetime import datetime, timezone

from sqlalchemy import func, select


def _to_naive_utc(dt: datetime) -> datetime:
    """Приводит datetime к naive UTC для PostgreSQL TIMESTAMP WITHOUT TIME ZONE."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.slot import Slot
from app.models.studio import Studio
from app.schemas.slot import SlotCreate, SlotUpdate


async def get_slot(db: AsyncSession, slot_id: int) -> Slot | None:
    """Получить слот по ID."""
    result = await db.execute(select(Slot).where(Slot.id == slot_id))
    return result.scalar_one_or_none()


async def get_slots(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    is_active: bool | None = None,
) -> list[Slot]:
    """
    Список слотов с фильтрами.

    studio_id — слоты конкретной студии (расписание)
    start_from, start_to — диапазон дат
    is_active — фильтр по статусу
    """
    query = select(Slot)
    if studio_id is not None:
        query = query.where(Slot.studio_id == studio_id)
    if start_from is not None:
        query = query.where(Slot.start_time >= _to_naive_utc(start_from))
    if start_to is not None:
        query = query.where(Slot.start_time <= _to_naive_utc(start_to))
    if is_active is not None:
        query = query.where(Slot.is_active == is_active)
    query = query.offset(skip).limit(limit).order_by(Slot.start_time.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_slots_count(
    db: AsyncSession,
    *,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    is_active: bool | None = None,
) -> int:
    """Подсчёт слотов для пагинации."""
    query = select(func.count()).select_from(Slot)
    if studio_id is not None:
        query = query.where(Slot.studio_id == studio_id)
    if start_from is not None:
        query = query.where(Slot.start_time >= _to_naive_utc(start_from))
    if start_to is not None:
        query = query.where(Slot.start_time <= _to_naive_utc(start_to))
    if is_active is not None:
        query = query.where(Slot.is_active == is_active)
    result = await db.execute(query)
    return result.scalar_one_or_none() or 0


async def get_bookings_count(db: AsyncSession, slot_id: int) -> int:
    """Количество подтверждённых бронирований в слоте."""
    from app.models.booking import BookingStatus

    result = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.slot_id == slot_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    return result.scalar_one_or_none() or 0


async def create_slot(db: AsyncSession, schema: SlotCreate) -> Slot:
    """
    Создать слот.

    Проверяет: студия существует, end_time > start_time.
    """
    from fastapi import HTTPException

    if schema.end_time <= schema.start_time:
        raise HTTPException(
            status_code=400,
            detail="Время окончания должно быть позже времени начала",
        )

    result = await db.execute(select(Studio).where(Studio.id == schema.studio_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")

    slot = Slot(
        studio_id=schema.studio_id,
        start_time=_to_naive_utc(schema.start_time),
        end_time=_to_naive_utc(schema.end_time),
        title=schema.title,
        description=schema.description,
        max_capacity=schema.max_capacity,
        price_cents=schema.price_cents,
    )
    db.add(slot)
    await db.flush()
    await db.refresh(slot)
    return slot


async def update_slot(
    db: AsyncSession,
    slot: Slot,
    schema: SlotUpdate,
) -> Slot:
    """
    Обновить слот.

    Проверяет end_time > start_time при обновлении времён.
    """
    from fastapi import HTTPException

    update_data = schema.model_dump(exclude_unset=True)
    start_time = update_data.get("start_time", slot.start_time)
    end_time = update_data.get("end_time", slot.end_time)
    if end_time <= start_time:
        raise HTTPException(
            status_code=400,
            detail="Время окончания должно быть позже времени начала",
        )
    for field, value in update_data.items():
        if field in ("start_time", "end_time") and value is not None:
            value = _to_naive_utc(value)
        setattr(slot, field, value)
    await db.flush()
    await db.refresh(slot)
    return slot


async def delete_slot(db: AsyncSession, slot: Slot) -> None:
    """Удалить слот. Cascade удалит бронирования."""
    await db.delete(slot)
    await db.flush()
