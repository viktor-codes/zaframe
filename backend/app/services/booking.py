"""
Бизнес-логика для бронирований.

Почему сервисный слой:
- Проверка вместимости слота
- Валидация (слот в будущем, не отменён)
- Переиспользование при webhook оплаты
"""

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.core.booking_holds import get_booking_reserved_until
from app.core.datetime_utils import ensure_utc, utc_now
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.uow import UnitOfWork
from app.models.booking import Booking, BookingStatus, BookingType
from app.models.user import User
from app.schemas.booking import (
    BookingCreate,
    BookingOwnerResponse,
    BookingSelfResponse,
)

DUPLICATE_BOOKING_MESSAGE = "You already have a booking for this session"

_ACTIVE_BOOKING_UNIQUE_INDEX_NAMES = frozenset(
    {
        "uq_bookings_slot_guest_email_active",
        "uq_bookings_slot_user_id_active",
    }
)


def _is_active_booking_unique_violation(exc: IntegrityError) -> bool:
    """True when PostgreSQL rejected a duplicate active booking insert."""
    orig = exc.orig
    if orig is None:
        return False
    constraint_name = getattr(orig, "constraint_name", None)
    if constraint_name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES:
        return True
    message = str(orig)
    return any(name in message for name in _ACTIVE_BOOKING_UNIQUE_INDEX_NAMES)


async def _ensure_no_active_booking_for_guest(
    uow: UnitOfWork,
    *,
    slot_id: int,
    guest_email: str,
    user_id: int | None = None,
) -> None:
    """Raise ValidationError when guest already has a non-cancelled booking on the slot."""
    if user_id is not None:
        existing_by_user = await uow.bookings.get_active_by_slot_and_user_id(slot_id, user_id)
        if existing_by_user is not None:
            raise ValidationError(DUPLICATE_BOOKING_MESSAGE)

    existing = await uow.bookings.get_active_by_slot_and_guest_email(slot_id, guest_email)
    if existing is not None:
        raise ValidationError(DUPLICATE_BOOKING_MESSAGE)


async def _persist_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """Insert booking; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add(booking)
    except IntegrityError as exc:
        if _is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise


async def _persist_bookings(uow: UnitOfWork, bookings: list[Booking]) -> list[Booking]:
    """Insert multiple bookings; map unique-index races to ConflictError."""
    try:
        return await uow.bookings.add_all(bookings)
    except IntegrityError as exc:
        if _is_active_booking_unique_violation(exc):
            raise ConflictError(DUPLICATE_BOOKING_MESSAGE) from exc
        raise


async def get_booking(uow: UnitOfWork, booking_id: int) -> Booking | None:
    """Получить бронирование по ID."""
    return await uow.bookings.get_by_id(booking_id)


async def get_booking_or_raise(uow: UnitOfWork, booking_id: int) -> Booking:
    """Получить бронирование по ID или выбросить NotFoundError."""
    booking = await uow.bookings.get_by_id(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    return booking


def is_own_booking(booking: Booking, user: User) -> bool:
    """True when booking belongs to the user (by user_id or guest_email)."""
    if booking.user_id is not None and booking.user_id == user.id:
        return True
    if booking.guest_email is not None:
        return booking.guest_email.strip().lower() == user.email.strip().lower()
    return False


def can_access_booking(
    booking: Booking,
    user: User,
    *,
    studio_owner_id: int | None,
) -> bool:
    """True when booking is the user's own or belongs to a studio they own."""
    if is_own_booking(booking, user):
        return True
    return studio_owner_id is not None and studio_owner_id == user.id


def map_booking_for_user(booking: Booking, user: User) -> BookingSelfResponse | BookingOwnerResponse:
    """
    Map ORM booking to the appropriate client response schema.

    Own bookings use BookingSelfResponse; studio-owner views use BookingOwnerResponse.
    """
    if is_own_booking(booking, user):
        return BookingSelfResponse.model_validate(booking)
    return BookingOwnerResponse.model_validate(booking)


async def get_booking_for_user_or_raise(
    uow: UnitOfWork,
    booking_id: int,
    user: User,
) -> Booking:
    """
    Load booking with slot+studio; allow own booking or studio owner.

    Returns 404 when the booking does not exist or the user has no access,
    so foreign booking IDs are not enumerable.
    """
    booking = await uow.bookings.get_by_id_with_slot_and_studio(booking_id)
    if booking is None:
        raise NotFoundError("Booking not found")
    studio_owner_id = None
    if booking.slot is not None and booking.slot.studio is not None:
        studio_owner_id = booking.slot.studio.owner_id
    if not can_access_booking(booking, user, studio_owner_id=studio_owner_id):
        raise NotFoundError("Booking not found")
    return booking


async def get_owner_bookings(
    uow: UnitOfWork,
    user: User,
    *,
    skip: int = 0,
    limit: int = 20,
    slot_id: int | None = None,
    status: str | None = None,
) -> list[Booking]:
    """Owner dashboard: bookings for slots in studios owned by the user."""
    return await uow.bookings.list_for_studio_owner(
        owner_id=user.id,
        skip=skip,
        limit=limit,
        slot_id=slot_id,
        status=status,
    )


async def get_owner_bookings_count(
    uow: UnitOfWork,
    user: User,
    *,
    slot_id: int | None = None,
    status: str | None = None,
) -> int:
    """Count bookings for studios owned by the user."""
    return await uow.bookings.count_for_studio_owner(
        owner_id=user.id,
        slot_id=slot_id,
        status=status,
    )


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
    status — pending, confirmed, cancelled, expired, completed
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


async def get_my_bookings(
    uow: UnitOfWork,
    *,
    user: User,
    skip: int = 0,
    limit: int = 50,
    include_guest_email: bool = True,
) -> list[Booking]:
    """
    Bookings list for personal cabinet (slot+studio embedded).

    include_guest_email=True merges legacy guest bookings by guest_email == user.email.
    """
    return await uow.bookings.list_my_with_slot_and_studio(
        skip=skip,
        limit=limit,
        user_id=user.id,
        user_email=user.email,
        include_guest_email=include_guest_email,
    )


async def attach_guest_bookings(
    uow: UnitOfWork,
    user: User,
    *,
    booking_id: int | None = None,
) -> int:
    """
    Link guest bookings to the authenticated user after OTP verify.

    Matches bookings by guest_email == user.email where user_id is still NULL.
    """
    return await uow.bookings.attach_guest_bookings_by_email(
        user_id=user.id,
        guest_email=user.email,
        booking_id=booking_id,
    )


async def create_booking(uow: UnitOfWork, schema: BookingCreate) -> Booking:
    """
    Создать гостевое бронирование.

    Проверяет:
    - слот существует и активен
    - слот в будущем
    - есть свободные места

    user_id проставляется после OTP verify (attach_guest_bookings).
    """
    slot = await uow.slots.get_by_id_for_update(schema.occurrence_id)
    if slot is None:
        raise NotFoundError("Slot not found")
    if not slot.is_bookable():
        raise ValidationError("Slot is not available for booking")

    now_utc = utc_now()
    slot_start = ensure_utc(slot.start_time)
    if slot_start <= now_utc:
        raise ValidationError("Cannot book a slot in the past")

    confirmed_count = await uow.bookings.count_confirmed_by_slot(slot.id)
    pending_count = await uow.bookings.count_pending_by_slot(slot.id, now=now_utc)
    if confirmed_count + pending_count >= slot.max_capacity:
        raise ValidationError("No seats available")

    await _ensure_no_active_booking_for_guest(
        uow,
        slot_id=schema.occurrence_id,
        guest_email=schema.guest_email,
    )

    booking = Booking(
        slot_id=schema.occurrence_id,
        guest_name=schema.guest_name,
        guest_email=schema.guest_email,
        guest_phone=schema.guest_phone,
        status=BookingStatus.PENDING,
        reserved_until=get_booking_reserved_until(now=now_utc),
        booking_type=getattr(schema, "booking_type", BookingType.SINGLE),
        service_id=getattr(schema, "service_id", None),
    )
    return await _persist_booking(uow, booking)


async def expire_stale_pending(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
) -> int:
    """
    Mark pending bookings with expired reserved_until as EXPIRED.

    Returns the number of bookings transitioned.
    """
    now_utc = now or utc_now()
    bookings = await uow.bookings.list_stale_pending(now=now_utc)
    for booking in bookings:
        booking.status = BookingStatus.EXPIRED
        booking.reserved_until = None
    if bookings:
        await uow.bookings.flush()
    return len(bookings)


async def complete_past_confirmed(
    uow: UnitOfWork,
    *,
    now: datetime | None = None,
) -> int:
    """
    Mark confirmed bookings as COMPLETED when their slot has ended.

    Uses slot.end_time < now (slot still in progress at exactly end_time).
    Returns the number of bookings transitioned.
    """
    now_utc = now or utc_now()
    bookings = await uow.bookings.list_past_confirmed(now=now_utc)
    for booking in bookings:
        booking.status = BookingStatus.COMPLETED
        booking.reserved_until = None
    if bookings:
        await uow.bookings.flush()
    return len(bookings)


async def cancel_booking(uow: UnitOfWork, booking: Booking) -> Booking:
    """
    Отменить бронирование.

    Только pending или confirmed можно отменить.
    """
    if booking.status == BookingStatus.CANCELLED:
        raise ValidationError("Booking is already cancelled")
    if booking.status in (BookingStatus.EXPIRED, BookingStatus.COMPLETED):
        raise ValidationError(f"Cannot cancel a {booking.status} booking")

    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = utc_now()
    booking.reserved_until = None
    return await uow.bookings.save(booking)
