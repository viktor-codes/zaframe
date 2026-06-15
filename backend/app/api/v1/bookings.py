"""
API роутер для бронирований.

Операции:
- POST /bookings — создать (гостевой режим)
- GET /bookings — список с фильтрами
- GET /bookings/{id} — одно бронирование
- PATCH /bookings/{id}/cancel — отменить
"""

from fastapi import APIRouter, Depends, Query, Request

from app.api.deps import get_current_user_required, get_uow
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.schemas import (
    BookingCreate,
    BookingListItem,
    BookingResponse,
    CourseBookingCreate,
    CourseBookingResponse,
)
from app.services.booking import (
    cancel_booking,
    create_booking,
    get_accessible_bookings,
    get_accessible_bookings_count,
    get_booking_or_raise_with_access,
    get_my_bookings,
)
from app.services.service import create_course_booking

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse | CourseBookingResponse, status_code=201)
@limiter.limit("10/minute")
async def create_booking_endpoint(
    request: Request,
    schema: BookingCreate | CourseBookingCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> BookingResponse | CourseBookingResponse:
    """
    Создать бронирование.

    Варианты:
    - разовое бронирование слота (BookingCreate)
    - покупка курса (CourseBookingCreate) — создаёт Order и N бронирований
    """
    if isinstance(schema, CourseBookingCreate):
        return await create_course_booking(uow, schema=schema)
    # Обычное разовое бронирование
    booking = await create_booking(uow, schema)  # type: ignore[arg-type]
    return booking


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    slot_id: int | None = Query(None, description="Фильтр по слоту"),
    user_id: int | None = Query(None, description="Фильтр по пользователю (только свой)"),
    guest_email: str | None = Query(None, description="Фильтр по email гостя (только свой)"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> list[BookingResponse]:
    """Список бронирований, доступных текущему пользователю."""
    bookings = await get_accessible_bookings(
        uow,
        user,
        skip=skip,
        limit=limit,
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )
    return bookings


@router.get("/my", response_model=list[BookingListItem])
async def list_my_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(50, ge=1, le=100, description="Максимум записей"),
    include_guest_email: bool = Query(
        True,
        description="Включать гостевые бронирования по совпадению guest_email с email пользователя",
    ),
) -> list[BookingListItem]:
    """
    Кабинетный список бронирований текущего пользователя (без N+1).

    Возвращает Booking + Slot + Studio, чтобы фронт не делал дополнительные запросы.
    """
    bookings = await get_my_bookings(
        uow,
        user=user,
        skip=skip,
        limit=limit,
        include_guest_email=include_guest_email,
    )
    # Map ORM -> response with explicit studio field.
    return [
        BookingListItem(
            **BookingResponse.model_validate(b).model_dump(),
            slot=b.slot,
            studio=b.slot.studio,
        )
        for b in bookings
        if getattr(b, "slot", None) is not None and getattr(b.slot, "studio", None) is not None
    ]


@router.get("/count")
async def count_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    slot_id: int | None = Query(None, description="Фильтр по слоту"),
    user_id: int | None = Query(None, description="Фильтр по пользователю (только свой)"),
    guest_email: str | None = Query(None, description="Фильтр по email гостя (только свой)"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество доступных бронирований (для пагинации)."""
    count = await get_accessible_bookings_count(
        uow,
        user,
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )
    return {"count": count}


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id(
    booking_id: int,
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
) -> BookingResponse:
    """Получить бронирование по ID (только своё или студии владельца)."""
    return await get_booking_or_raise_with_access(uow, booking_id, user)


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking_endpoint(
    booking_id: int,
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
) -> BookingResponse:
    """Отменить бронирование (только своё или студии владельца)."""
    booking = await get_booking_or_raise_with_access(uow, booking_id, user)
    return await cancel_booking(uow, booking)
