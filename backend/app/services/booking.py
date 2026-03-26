"""
Бизнес-логика для бронирований.

Почему сервисный слой:
- Проверка вместимости слота
- Валидация (слот в будущем, не отменён)
- Переиспользование при webhook оплаты
"""

from datetime import UTC, datetime

from app.core.exceptions import NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.schemas.booking import BookingCreate, BookingUpdate


async def get_booking(uow: UnitOfWork, booking_id: int) -> Booking | None:
    """Получить бронирование по ID."""
    return await uow.bookings.get_by_id(booking_id)


async def get_booking_or_raise(uow: UnitOfWork, booking_id: int) -> Booking:
    """Получить бронирование по ID или выбросить NotFoundError."""
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


async def get_bookings(
    uow: UnitOfWork,
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
    return await uow.bookings.list_(
        skip=skip,
        limit=limit,
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )


async def get_bookings_count(
    uow: UnitOfWork,
    *,
    slot_id: int | None = None,
    user_id: int | None = None,
    guest_email: str | None = None,
    status: str | None = None,
) -> int:
    """Подсчёт бронирований для пагинации."""
    return await uow.bookings.count(
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )


async def create_booking(uow: UnitOfWork, schema: BookingCreate) -> Booking:
    """
    Создать гостевное бронирование.

    Проверяет:
    - слот существует и активен
    - слот в будущем
    - есть свободные места

    guest_session_id — опционально (добавим при интеграции Magic Link).
    """
    slot = await uow.slots.get_by_id_for_update(schema.slot_id)
    if slot is None:
        raise NotFoundError("Slot not found")
    if not slot.is_active:
        raise ValidationError("Slot is not available for booking")

    now_utc = datetime.now(UTC)
    slot_start = slot.start_time
    if slot_start.tzinfo is None:
        slot_start = slot_start.replace(tzinfo=UTC)
    if slot_start <= now_utc:
        raise ValidationError("Cannot book a slot in the past")

    confirmed_count = await uow.bookings.count_confirmed_by_slot(slot.id)
    pending_count = await uow.bookings.count_pending_by_slot(slot.id)
    if confirmed_count + pending_count >= slot.max_capacity:
        raise ValidationError("No seats available")

    booking = Booking(
        slot_id=schema.slot_id,
        guest_name=schema.guest_name,
        guest_email=schema.guest_email,
        guest_phone=schema.guest_phone,
        status=BookingStatus.PENDING,
        booking_type=getattr(schema, "booking_type", BookingType.SINGLE),
        service_id=getattr(schema, "service_id", None),
    )
    uow.session.add(booking)
    await uow.session.flush()
    await uow.session.refresh(booking)
    return booking


async def cancel_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """
    Отменить бронирование.

    Только pending или confirmed можно отменить.
    """
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Booking is already cancelled")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = datetime.now(UTC)
    await uow.session.flush()
    await uow.session.refresh(booking)
    return booking


async def update_booking(
    uow: UnitOfWork,
    booking: Booking,
    schema: BookingUpdate,
) -> Booking:
    """Обновить бронирование (статус, payment)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(booking, field, value)
    await uow.session.flush()
    await uow.session.refresh(booking)
    return booking
