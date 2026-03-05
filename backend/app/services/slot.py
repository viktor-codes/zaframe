"""
Бизнес-логика для слотов (расписание).

Почему сервисный слой:
- Роутеры остаются тонкими
- Валидация (end_time > start_time) в одном месте
- Переиспользование при бронировании
"""
from datetime import datetime, timezone

from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.slot import Slot
from app.schemas.slot import SlotCreate, SlotUpdate


def _to_naive_utc(dt: datetime) -> datetime:
    """Приводит datetime к naive UTC для PostgreSQL TIMESTAMP WITHOUT TIME ZONE."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


async def get_slot(uow: UnitOfWork, slot_id: int) -> Slot | None:
    """Получить слот по ID."""
    return await uow.slots.get_by_id(slot_id)


async def get_slot_or_raise(uow: UnitOfWork, slot_id: int) -> Slot:
    """Получить слот по ID или выбросить NotFoundError."""
    slot = await uow.slots.get_by_id(slot_id)
    if slot is None:
        raise NotFoundError("Слот не найден")
    return slot


async def get_slots(
    uow: UnitOfWork,
    *,
    skip: int = 0,
    limit: int = 20,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    is_active: bool | None = None,
) -> list[Slot]:
    """Список слотов с фильтрами."""
    return await uow.slots.list_(
        skip=skip,
        limit=limit,
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        is_active=is_active,
    )


async def get_slots_count(
    uow: UnitOfWork,
    *,
    studio_id: int | None = None,
    start_from: datetime | None = None,
    start_to: datetime | None = None,
    is_active: bool | None = None,
) -> int:
    """Подсчёт слотов для пагинации."""
    return await uow.slots.count(
        studio_id=studio_id,
        start_from=start_from,
        start_to=start_to,
        is_active=is_active,
    )


async def get_bookings_count(uow: UnitOfWork, slot_id: int) -> int:
    """Количество подтверждённых бронирований в слоте."""
    return await uow.bookings.count_confirmed_by_slot(slot_id)


async def create_slot(uow: UnitOfWork, schema: SlotCreate) -> Slot:
    """Создать слот. Проверяет: студия существует, end_time > start_time."""
    if schema.end_time <= schema.start_time:
        raise ValidationError("Время окончания должно быть позже времени начала")
    if await uow.studios.get_by_id(schema.studio_id) is None:
        raise NotFoundError("Студия не найдена")

    slot = Slot(
        studio_id=schema.studio_id,
        start_time=_to_naive_utc(schema.start_time),
        end_time=_to_naive_utc(schema.end_time),
        title=schema.title,
        description=schema.description,
        max_capacity=schema.max_capacity,
        price_cents=schema.price_cents,
    )
    uow.session.add(slot)
    await uow.session.flush()
    await uow.session.refresh(slot)
    return slot


async def update_slot(
    uow: UnitOfWork,
    slot: Slot,
    schema: SlotUpdate,
) -> Slot:
    """Обновить слот. Проверяет end_time > start_time при обновлении времён."""
    update_data = schema.model_dump(exclude_unset=True)
    start_time = update_data.get("start_time", slot.start_time)
    end_time = update_data.get("end_time", slot.end_time)
    if end_time <= start_time:
        raise ValidationError("Время окончания должно быть позже времени начала")
    for field, value in update_data.items():
        if field in ("start_time", "end_time") and value is not None:
            value = _to_naive_utc(value)
        setattr(slot, field, value)
    await uow.session.flush()
    await uow.session.refresh(slot)
    return slot


async def delete_slot(uow: UnitOfWork, slot: Slot) -> None:
    """Удалить слот. Cascade удалит бронирования."""
    await uow.session.delete(slot)
    await uow.session.flush()
