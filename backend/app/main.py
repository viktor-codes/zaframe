"""
ZaFrame API entrypoint.

`main.py` stays minimal: create the `FastAPI` app, include routers, and define
the lifespan hook. All business logic lives in `core/`, `api/`, and `services/`.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.v1 import auth, bookings, health, payments, services, slots, studios
from app.api.v1.endpoints import search
from app.api.webhooks import router as webhooks_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.core.middleware.logging_middleware import (
    REQUEST_ID_STATE_KEY,
    RequestLoggingMiddleware,
)
from app.core.rate_limit import limiter


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response


# === Lifespan Context Manager ===
# Manages the application's lifecycle: startup and shutdown events.
# Why `lifespan` instead of `@app.on_event`:
# - Recommended way in FastAPI (`on_event` is deprecated)
# - More explicit resource management via a context manager
# - Easier to test and mock
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """
    Lifespan context manager for DB and logging setup.

    On startup: initialize logging (and optionally run readiness checks).
    On shutdown: close all DB connections.
    """
    setup_logging()
    yield
    await engine.dispose()


# Use settings from `config.py` instead of hardcoding.
# Centralize `title` and `version` and allow overrides via `.env`.
# `lifespan=lifespan` wires the lifecycle management.
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """429 in API format: detail + rate limit headers (X-RateLimit-*)."""
    request_id = _request_id(request)
    response = JSONResponse(
        status_code=429,
        content=_error_body(
            detail="Too many requests. Please try again later.",
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


# === Exception handlers (domain exceptions → HTTP + logging) ===
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
    """Map domain exceptions to HTTP responses and log the failure."""
    logger = structlog.get_logger(__name__)
    request_id = _request_id(request)
    logger.warning(
        "app_error",
        request_id=request_id,
        status=exc.status_code,
        detail=exc.detail,
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
    """Unhandled exception: log traceback and return 500."""
    logger = structlog.get_logger(__name__)
    request_id = _request_id(request)
    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        exc_type=type(exc).__name__,
        msg=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content=_error_body(
            detail="Internal server error",
            status_code=500,
            request_id=request_id,
            problem_type="internal-error",
        ),
    )


app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# === Logging middleware (request_id + request/response logging) ===
# Add it first so it can wrap all requests (the last added runs first).
app.add_middleware(RequestLoggingMiddleware)

# === Security headers Middleware ===
app.add_middleware(SecurityHeadersMiddleware)

# === CORS middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# One router — two prefixes: no duplicated routes.
# 1) Root: `/` and `/health` for load balancers, k8s probes, and monitoring.
# 2) Versioned API: `/api/v1/` and `/api/v1/health` for clients.
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
