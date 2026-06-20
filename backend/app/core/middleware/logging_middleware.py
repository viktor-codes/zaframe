"""Request logging middleware.

Adds `X-Request-ID` to every request/response and logs structured request
completion events via `structlog`.
"""

import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.observability import safe_log_fields

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_KEY = "request_id"
USER_ID_STATE_KEY = "user_id"
MAX_REQUEST_ID_LENGTH = 128


def _is_valid_request_id(value: str) -> bool:
    return (
        0 < len(value) <= MAX_REQUEST_ID_LENGTH
        and all(char.isprintable() and char not in "\r\n\t" for char in value)
    )


def _get_request_id(request: Request) -> str:
    """Read `X-Request-ID` from headers or generate a new one."""
    raw = request.headers.get(REQUEST_ID_HEADER)
    if raw:
        request_id = raw.strip()
        if _is_valid_request_id(request_id):
            return request_id
    return str(uuid.uuid4())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Add `request_id` and log each HTTP request after processing.

    Expects `request.state.user_id` to be optionally set by auth dependencies.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        logger = structlog.get_logger(__name__)
        request_id = _get_request_id(request)
        setattr(request.state, REQUEST_ID_STATE_KEY, request_id)
        start = time.perf_counter()

        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            logger.info(
                "request_started",
                **safe_log_fields(
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "request_id": request_id,
                    }
                ),
            )
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000
            status = response.status_code
            user_id = getattr(request.state, USER_ID_STATE_KEY, None)

            common_fields = {
                "method": request.method,
                "path": request.url.path,
                "status": status,
                "duration_ms": duration_ms,
                "request_id": request_id,
                "user_id": user_id,
            }
            event = "request_finished"
            if status >= 500:
                logger.error(event, **common_fields)
            elif status in (401, 403, 429):
                logger.warning(event, **common_fields)
            else:
                logger.info(event, **common_fields)

            if REQUEST_ID_HEADER not in response.headers:
                response.headers[REQUEST_ID_HEADER] = request_id
            return response
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            user_id = getattr(request.state, USER_ID_STATE_KEY, None)
            logger.error(
                "request_failed",
                **safe_log_fields(
                    {
                        "method": request.method,
                        "path": request.url.path,
                        "duration_ms": duration_ms,
                        "request_id": request_id,
                        "user_id": user_id,
                    }
                ),
            )
            raise
        finally:
            structlog.contextvars.clear_contextvars()
