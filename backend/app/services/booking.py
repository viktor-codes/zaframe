"""
Бизнес-логика для бронирований.

Почему сервисный слой:
- Проверка вместимости слота
- Валидация (слот в будущем, не отменён)
- Переиспользование при webhook оплаты
"""
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus, BookingType
from app.models.slot import Slot
from app.schemas.booking import BookingCreate, BookingUpdate


async def get_booking(db: AsyncSession, booking_id: int) -> Booking | None:
    """Получить бронирование по ID."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def get_bookings(
    db: AsyncSession,
    *,
    skip: int = 0,
    limit: int = 20,
    slot_id: int | None = None,
    user_id: int | None = None,
    guest_email: str | None = None,
    status: str | None = None,
) -> list[Booking]:
    """
    Список бронирований с фильтрами.

    slot_id — бронирования слота
    user_id — бронирования пользователя
    guest_email — бронирования гостя (до активации)
    status — pending, confirmed, cancelled
    """
    query = select(Booking)
    if slot_id is not None:
        query = query.where(Booking.slot_id == slot_id)
    if user_id is not None:
        query = query.where(Booking.user_id == user_id)
    if guest_email is not None:
        query = query.where(Booking.guest_email == guest_email)
    if status is not None:
        query = query.where(Booking.status == status)
    query = query.offset(skip).limit(limit).order_by(Booking.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_bookings_count(
    db: AsyncSession,
    *,
    slot_id: int | None = None,
    user_id: int | None = None,
    guest_email: str | None = None,
    status: str | None = None,
) -> int:
    """Подсчёт бронирований для пагинации."""
    query = select(func.count()).select_from(Booking)
    if slot_id is not None:
        query = query.where(Booking.slot_id == slot_id)
    if user_id is not None:
        query = query.where(Booking.user_id == user_id)
    if guest_email is not None:
        query = query.where(Booking.guest_email == guest_email)
    if status is not None:
        query = query.where(Booking.status == status)
    result = await db.execute(query)
    return result.scalar_one_or_none() or 0


async def _get_confirmed_bookings_count(db: AsyncSession, slot_id: int) -> int:
    """Количество подтверждённых бронирований в слоте."""
    result = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.slot_id == slot_id,
            Booking.status == BookingStatus.CONFIRMED,
        )
    )
    return result.scalar_one_or_none() or 0


async def create_booking(db: AsyncSession, schema: BookingCreate) -> Booking:
    """
    Создать гостевное бронирование.

    Проверяет:
    - слот существует и активен
    - слот в будущем
    - есть свободные места

    guest_session_id — опционально (добавим при интеграции Magic Link).
    """
    result = await db.execute(select(Slot).where(Slot.id == schema.slot_id))
    slot = result.scalar_one_or_none()
    if slot is None:
        raise HTTPException(status_code=404, detail="Слот не найден")
    if not slot.is_active:
        raise HTTPException(status_code=400, detail="Слот недоступен для бронирования")

    if slot.start_time <= datetime.utcnow():
        raise HTTPException(status_code=400, detail="Нельзя бронировать прошедший слот")

    confirmed_count = await _get_confirmed_bookings_count(db, slot.id)
    # Учитываем и pending — одно место на бронирование
    pending_count = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.slot_id == slot.id,
            Booking.status == BookingStatus.PENDING,
        )
    )
    total_bookings = confirmed_count + (pending_count.scalar_one_or_none() or 0)
    if total_bookings >= slot.max_capacity:
        raise HTTPException(status_code=400, detail="Нет свободных мест")

    booking = Booking(
        slot_id=schema.slot_id,
        guest_name=schema.guest_name,
        guest_email=schema.guest_email,
        guest_phone=schema.guest_phone,
        status=BookingStatus.PENDING,
        booking_type=getattr(schema, "booking_type", BookingType.SINGLE),
        service_id=getattr(schema, "service_id", None),
    )
    db.add(booking)
    await db.flush()
    await db.refresh(booking)
    return booking


async def cancel_booking(db: AsyncSession, booking: Booking) -> Booking:
    """
    Отменить бронирование.

    Только pending или confirmed можно отменить.
    """
    if booking.status == BookingStatus.CANCELLED:
        raise HTTPException(status_code=400, detail="Бронирование уже отменено")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.utcnow()
    await db.flush()
    await db.refresh(booking)
    return booking


async def update_booking(
    db: AsyncSession,
    booking: Booking,
    schema: BookingUpdate,
) -> Booking:
    """Обновить бронирование (статус, payment)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    await db.flush()
    await db.refresh(booking)
    return booking
