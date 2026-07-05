"""
ZeeFrame API entrypoint.

`main.py` stays minimal: create the `FastAPI` app, include routers, and define
the lifespan hook. All business logic lives in `core/`, `api/`, and `modules/`.
"""

import traceback
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.api.router import register_routers
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import AppError
from app.core.logging_config import setup_logging
from app.core.middleware.logging_middleware import (
    REQUEST_ID_HEADER,
    REQUEST_ID_STATE_KEY,
    RequestLoggingMiddleware,
)
from app.core.rate_limit import limiter

API_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
)
HSTS_HEADER_VALUE = "max-age=31536000; includeSubDomains"
DOCS_PATH_PREFIXES = ("/docs", "/redoc")
DOCS_PATHS = ("/openapi.json",)


def _is_docs_path(path: str) -> bool:
    return path in DOCS_PATHS or path.startswith(DOCS_PATH_PREFIXES)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add baseline security headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        if settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", HSTS_HEADER_VALUE)
        if not _is_docs_path(request.url.path):
            response.headers.setdefault("Content-Security-Policy", API_CONTENT_SECURITY_POLICY)
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
    response = _problem_response(
        status_code=429,
        content=_error_body(
            detail="Too many requests. Please try again later.",
            status_code=429,
            request_id=request_id,
            problem_type="rate-limit-exceeded",
        ),
        request_id=request_id,
    )
    if hasattr(request.state, "view_rate_limit"):
        response = request.app.state.limiter._inject_headers(
            response, request.state.view_rate_limit
        )
    return response


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # pyright: ignore[reportArgumentType]  # WHY: Starlette handler union is wider than HTTP-only handlers


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
    503: "Service Unavailable",
}


def _error_body(
    *,
    detail: str,
    status_code: int,
    request_id: str | None = None,
    problem_type: str = "about:blank",
) -> dict[str, Any]:
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


def _problem_response(
    *,
    status_code: int,
    content: dict[str, Any],
    request_id: str | None,
) -> JSONResponse:
    """Create Problem JSON and keep X-Request-ID present on error responses."""
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(status_code=status_code, content=content, headers=headers)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Map domain exceptions to HTTP responses and log the failure."""
    logger = structlog.get_logger(__name__)
    request_id = _request_id(request)
    logger.warning(
        "app_error",
        request_id=request_id,
        status=exc.status_code,
        error_type=type(exc).__name__,
    )
    return _problem_response(
        status_code=exc.status_code,
        content=_error_body(
            detail=exc.detail,
            status_code=exc.status_code,
            request_id=request_id,
            problem_type=f"app-error:{type(exc).__name__}",
        ),
        request_id=request_id,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Unhandled exception: log traceback and return 500."""
    logger = structlog.get_logger(__name__)
    request_id = _request_id(request)
    stack = "\n".join(
        f'File "{frame.filename}", line {frame.lineno}, in {frame.name}'
        for frame in traceback.extract_tb(exc.__traceback__)
    )
    logger.error(
        "unhandled_exception",
        request_id=request_id,
        exc_type=type(exc).__name__,
        stack=stack,
    )
    return _problem_response(
        status_code=500,
        content=_error_body(
            detail="Internal server error",
            status_code=500,
            request_id=request_id,
            problem_type="internal-error",
        ),
        request_id=request_id,
    )


app.add_exception_handler(AppError, app_error_handler)  # pyright: ignore[reportArgumentType]  # WHY: Starlette handler union is wider than HTTP-only handlers
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

register_routers(app)
