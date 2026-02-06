"""
Роутер для health-check и корневого эндпоинта.

Почему отдельный файл: даже простые эндпоинты лучше выносить в роутеры.
Это упрощает main.py и позволяет масштабировать API (добавлять auth, bookings и т.д.)
без раздувания одной точки входа.
"""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to ZaFrame API - Irish Dance & Yoga Booking"}


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
