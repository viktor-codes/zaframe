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
from app.api.mappers.service import map_course_booking_result
from app.core.rate_limit import limiter
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.booking import (
    cancel_booking,
    create_booking,
    get_booking_for_user_or_raise,
    get_my_bookings,
    get_owner_bookings,
    get_owner_bookings_count,
    map_booking_created_response,
    map_booking_for_user,
)
from app.modules.booking.order import CourseBookingInput, create_course_booking
from app.schemas import (
    BookingCreate,
    BookingCreatedResponse,
    BookingOwnerResponse,
    BookingSelfListItem,
    BookingSelfResponse,
    CourseBookingCreate,
    CourseBookingResponse,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post(
    "",
    response_model=BookingCreatedResponse | CourseBookingResponse,
    status_code=201,
)
@limiter.limit("10/minute")
async def create_booking_endpoint(
    request: Request,
    schema: BookingCreate | CourseBookingCreate,
    uow: UnitOfWork = Depends(get_uow),
) -> BookingCreatedResponse | CourseBookingResponse:
    """
    Создать бронирование.

    Варианты:
    - разовое бронирование слота (BookingCreate)
    - покупка курса (CourseBookingCreate) — создаёт Order и N бронирований
    """
    if isinstance(schema, CourseBookingCreate):
        result = await create_course_booking(
            uow,
            data=CourseBookingInput(
                service_id=schema.service_id,
                guest_name=schema.guest_name,
                guest_email=schema.guest_email,
                guest_phone=schema.guest_phone,
            ),
        )
        return map_course_booking_result(result)
    booking = await create_booking(uow, schema)  # type: ignore[arg-type]
    return map_booking_created_response(booking)


@router.get("", response_model=list[BookingOwnerResponse])
async def list_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    occurrence_id: int | None = Query(None, description="Фильтр по слоту"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> list[BookingOwnerResponse]:
    """Список бронирований студий, которыми владеет текущий пользователь."""
    bookings = await get_owner_bookings(
        uow,
        user,
        skip=skip,
        limit=limit,
        occurrence_id=occurrence_id,
        status=status,
    )
    return [BookingOwnerResponse.model_validate(b) for b in bookings]


@router.get("/my", response_model=list[BookingSelfListItem])
async def list_my_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(50, ge=1, le=100, description="Максимум записей"),
    include_guest_email: bool = Query(
        True,
        description="Включать гостевые бронирования по совпадению guest_email с email пользователя",
    ),
) -> list[BookingSelfListItem]:
    """
    Кабинетный список бронирований текущего пользователя (без N+1).

    Возвращает Booking + Occurrence + Studio, чтобы фронт не делал дополнительные запросы.
    """
    bookings = await get_my_bookings(
        uow,
        user=user,
        skip=skip,
        limit=limit,
        include_guest_email=include_guest_email,
    )
    return [
        BookingSelfListItem(
            **BookingSelfResponse.model_validate(b).model_dump(),
            occurrence=b.occurrence,
            studio=b.occurrence.studio,
        )
        for b in bookings
        if getattr(b, "occurrence", None) is not None and getattr(b.occurrence, "studio", None) is not None
    ]


@router.get("/count")
async def count_bookings(
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
    occurrence_id: int | None = Query(None, description="Фильтр по слоту"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество бронирований студий владельца (для пагинации)."""
    count = await get_owner_bookings_count(
        uow,
        user,
        occurrence_id=occurrence_id,
        status=status,
    )
    return {"count": count}


@router.get("/{booking_id}", response_model=BookingSelfResponse | BookingOwnerResponse)
async def get_booking_by_id(
    booking_id: int,
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
) -> BookingSelfResponse | BookingOwnerResponse:
    """Получить бронирование по ID (только своё или студии владельца)."""
    booking = await get_booking_for_user_or_raise(uow, booking_id, user)
    return map_booking_for_user(booking, user)


@router.patch(
    "/{booking_id}/cancel",
    response_model=BookingSelfResponse | BookingOwnerResponse,
)
async def cancel_booking_endpoint(
    booking_id: int,
    uow: UnitOfWork = Depends(get_uow),
    user: User = Depends(get_current_user_required),
) -> BookingSelfResponse | BookingOwnerResponse:
    """Отменить бронирование (только своё или студии владельца)."""
    booking = await get_booking_for_user_or_raise(uow, booking_id, user)
    cancelled = await cancel_booking(uow, booking)
    return map_booking_for_user(cancelled, user)
