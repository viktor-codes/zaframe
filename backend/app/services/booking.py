"""
Бизнес-логика для бронирований.

Почему сервисный слой:
- Проверка вместимости слота
- Валидация (слот в будущем, не отменён)
- Переиспользование при webhook оплаты
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.slot import Slot
from app.schemas.booking import BookingCreate, BookingUpdate


async def get_booking(db: AsyncSession, booking_id: int) -> Booking | None:
    """Получить бронирование по ID."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    return result.scalar_one_or_none()


async def get_booking_or_raise(db: AsyncSession, booking_id: int) -> Booking:
    """Получить бронирование по ID или выбросить NotFoundError."""
    booking = await get_booking(db, booking_id)
    if booking is None:
        raise NotFoundError("Бронирование не найдено")
    return booking


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


async def create_booking(uow: UnitOfWork, schema: BookingCreate) -> Booking:
    """
    Создать гостевное бронирование.

    Проверяет:
    - слот существует и активен
    - слот в будущем
    - есть свободные места

    guest_session_id — опционально (добавим при интеграции Magic Link).
    """
    db = uow.session
    # Блокируем слот на время проверки и создания бронирования,
    # чтобы избежать гонок при одновременных запросах.
    result = await db.execute(
        select(Slot).where(Slot.id == schema.slot_id).with_for_update()
    )
    slot = result.scalar_one_or_none()
    if slot is None:
        raise NotFoundError("Слот не найден")
    if not slot.is_active:
        raise ValidationError("Слот недоступен для бронирования")

    now_utc = datetime.now(timezone.utc)
    slot_start = slot.start_time
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=timezone.utc)
    if slot_start <= now_utc:
        raise ValidationError("Нельзя бронировать прошедший слот")

    confirmed_count = await _get_confirmed_bookings_count(db, slot.id)
    # Учитываем и pending — одно место на бронирование
    pending_result = await db.execute(
        select(func.count()).select_from(Booking).where(
            Booking.slot_id == slot.id,
            Booking.status == BookingStatus.PENDING,
        )
    )
    total_bookings = confirmed_count + (pending_result.scalar_one_or_none() or 0)
    if total_bookings >= slot.max_capacity:
        raise ValidationError("Нет свободных мест")

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


async def cancel_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """
    Отменить бронирование.

    Только pending или confirmed можно отменить.
    """
    db = uow.session
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Бронирование уже отменено")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(booking)
    return booking


async def update_booking(
    uow: UnitOfWork,
    booking: Booking,
    schema: BookingUpdate,
) -> Booking:
    """Обновить бронирование (статус, payment)."""
    db = uow.session
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    await db.flush()
    await db.refresh(booking)
    return booking
