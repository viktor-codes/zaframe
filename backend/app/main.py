"""
Точка входа приложения ZaFrame API.

main.py остаётся минимальным: создание app, подключение роутеров, lifespan.
Вся логика — в модулях core/, api/, services/.
"""
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.api.v1 import auth, bookings, health, payments, services, slots, studios
from app.api.v1.endpoints import search
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from app.core.middleware.logging_middleware import (
    REQUEST_ID_STATE_KEY,
    RequestLoggingMiddleware,
)

logger = logging.getLogger(__name__)


# === Lifespan Context Manager ===
# Управляет жизненным циклом приложения: startup и shutdown события.
# Почему lifespan вместо @app.on_event:
# - Рекомендуемый способ в FastAPI (on_event deprecated)
# - Более явное управление ресурсами через context manager
# - Проще тестировать и мокировать
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager для управления подключением к БД и логированием.
    
    При старте: настройка логирования, при необходимости — проверка БД.
    При остановке: закрываем все соединения с БД.
    """
    setup_logging()
    yield
    await engine.dispose()


# Используем настройки из config.py вместо хардкода.
# Теперь title и version централизованы и могут быть переопределены через .env
# lifespan=lifespan — подключаем управление жизненным циклом
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 в формате API: detail + заголовки лимита (X-RateLimit-*)."""
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=429,
        content=_error_body(
            detail="Превышен лимит запросов. Попробуйте позже.",
            status_code=429,
            request_id=request_id,
            problem_type="rate-limit-exceeded",
        ),
    )
    if hasattr(request.state, "view_rate_limit"):
        response = request.app.state.limiter._inject_headers(
            response, request.state.view_rate_limit
        )
    return response


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# === Exception handlers (доменные исключения → HTTP + логирование) ===
_STATUS_TITLES: dict[int, str] = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    409: "Conflict",
    422: "Unprocessable Entity",
    429: "Too Many Requests",
    500: "Internal Server Error",
}


def _error_body(
    *,
    detail: str,
    status_code: int,
    request_id: str | None = None,
    problem_type: str = "about:blank",
) -> dict:
    """RFC 7807 Problem JSON."""
    return {
        "type": problem_type,
        "title": _STATUS_TITLES.get(status_code, "Error"),
        "status": status_code,
        "detail": detail,
        **({"request_id": request_id} if request_id else {}),
    }


def _request_id(request: Request) -> str | None:
    return getattr(request.state, REQUEST_ID_STATE_KEY, None)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Маппинг доменных исключений в HTTP-ответ и лог ошибки."""
    request_id = _request_id(request)
    logger.warning(
        "app_error request_id=%s status=%s detail=%s",
        request_id,
        exc.status_code,
        exc.detail,
        exc_info=False,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body(
            detail=exc.detail,
            status_code=exc.status_code,
            request_id=request_id,
            problem_type=f"app-error:{type(exc).__name__}",
        ),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Необработанное исключение: лог с traceback и ответ 500."""
    request_id = _request_id(request)
    logger.exception(
        "unhandled_exception request_id=%s type=%s msg=%s",
        request_id,
        type(exc).__name__,
        str(exc),
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(
            detail="Внутренняя ошибка сервера",
            status_code=500,
            request_id=request_id,
            problem_type="internal-error",
        ),
    )


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# === Logging middleware (request_id + лог запроса/ответа) ===
# Добавляем первым, чтобы оборачивать все запросы (последний добавленный выполняется первым).
app.add_middleware(RequestLoggingMiddleware)

# === CORS Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Один роутер — два префикса: без дублирования кода.
# 1) Корень: / и /health — для load balancer'ов, k8s probes, мониторинга.
# 2) Версионированный API: /api/v1/ и /api/v1/health — для клиентов.
app.include_router(health.router)
app.include_router(health.router, prefix="/api/v1")
app.include_router(studios.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(slots.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(webhooks_router)
app.include_router(auth.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")