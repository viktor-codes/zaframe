
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to ZaFrame API - Irish Dance & Yoga Booking"}


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
