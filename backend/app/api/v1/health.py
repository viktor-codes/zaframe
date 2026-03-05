"""
Эндпоинты здоровья: liveness (/health) и readiness (/health/ready).

/health — простой "жив ли процесс", для load balancer.
/health/ready — готов ли принимать трафик: проверка БД, опционально Stripe/Resend.
"""
import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Response

from app.core.config import settings
from app.core.database import engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to ZaFrame API - Irish Dance & Yoga Booking"}


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness: процесс запущен. Не проверяет зависимости."""
    return {"status": "ok"}


async def _check_database() -> bool:
    """Проверка подключения к БД (SELECT 1)."""
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning("Readiness DB check failed: %s", e)
        return False


def _check_stripe_sync() -> bool:
    """Проверка доступности Stripe (лёгкий запрос). Вызывать в thread — SDK синхронный."""
    if not settings.STRIPE_SECRET_KEY:
        return True  # не настроен — не проверяем
    try:
        import stripe

        stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY).v1.balance.retrieve()
        return True
    except Exception as e:
        logger.warning("Readiness Stripe check failed: %s", e)
        return False


async def _check_stripe() -> bool:
    """Асинхронная обёртка для синхронного Stripe SDK."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _check_stripe_sync)


def _check_resend_configured() -> bool:
    """Resend: проверяем только наличие ключа (API не даёт лёгкого ping)."""
    return bool(settings.RESEND_API_KEY)


@router.get("/health/ready")
async def readiness(response: Response) -> dict[str, Any]:
    """
    Readiness: готов ли сервис принимать трафик.

    Проверяет:
    - БД — обязательно; при ошибке возвращает 503.
    - Stripe — если STRIPE_SECRET_KEY задан, один лёгкий запрос.
    - Resend — только факт настройки ключа.

    Используется k8s readinessProbe, load balancer и т.п.
    """
    checks: dict[str, str] = {}
    all_ok = True

    db_ok = await _check_database()
    checks["database"] = "ok" if db_ok else "fail"
    if not db_ok:
        response.status_code = 503
        return {"status": "unready", "checks": checks}

    if settings.STRIPE_SECRET_KEY:
        stripe_ok = await _check_stripe()
        checks["stripe"] = "ok" if stripe_ok else "fail"
    else:
        checks["stripe"] = "skip"

    if settings.RESEND_API_KEY:
        checks["resend"] = "configured"
    else:
        checks["resend"] = "skip"

    # 503 только при недоступности БД; Stripe/Resend — в checks для мониторинга
    return {
        "status": "ready",
        "checks": checks,
    }
