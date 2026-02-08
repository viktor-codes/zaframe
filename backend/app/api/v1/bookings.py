"""
API роутер для бронирований.

Операции:
- POST /bookings — создать (гостевой режим)
- GET /bookings — список с фильтрами
- GET /bookings/{id} — одно бронирование
- PATCH /bookings/{id}/cancel — отменить
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.booking import BookingCreate, BookingResponse
from app.services.booking import (
    cancel_booking,
    create_booking,
    get_booking,
    get_bookings,
    get_bookings_count,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("", response_model=BookingResponse, status_code=201)
async def create_booking_endpoint(
    schema: BookingCreate,
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """
    Создать бронирование (гостевой режим).

    Проверяет: слот существует, активен, в будущем, есть места.
    """
    booking = await create_booking(db, schema)
    return booking


@router.get("", response_model=list[BookingResponse])
async def list_bookings(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0, description="Пропустить N записей"),
    limit: int = Query(20, ge=1, le=100, description="Максимум записей"),
    slot_id: int | None = Query(None, description="Фильтр по слоту"),
    user_id: int | None = Query(None, description="Фильтр по пользователю"),
    guest_email: str | None = Query(None, description="Фильтр по email гостя"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> list[BookingResponse]:
    """Список бронирований с фильтрами."""
    bookings = await get_bookings(
        db,
        skip=skip,
        limit=limit,
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )
    return bookings


@router.get("/count")
async def count_bookings(
    db: AsyncSession = Depends(get_db),
    slot_id: int | None = Query(None, description="Фильтр по слоту"),
    user_id: int | None = Query(None, description="Фильтр по пользователю"),
    guest_email: str | None = Query(None, description="Фильтр по email гостя"),
    status: str | None = Query(None, description="Фильтр по статусу"),
) -> dict[str, int]:
    """Количество бронирований (для пагинации)."""
    count = await get_bookings_count(
        db,
        slot_id=slot_id,
        user_id=user_id,
        guest_email=guest_email,
        status=status,
    )
    return {"count": count}


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking_by_id(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Получить бронирование по ID."""
    booking = await get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return booking


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking_endpoint(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Отменить бронирование."""
    booking = await get_booking(db, booking_id)
    if booking is None:
        raise HTTPException(status_code=404, detail="Бронирование не найдено")
    return await cancel_booking(db, booking)
