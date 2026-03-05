"""
Middleware: request_id и логирование запроса/ответа.

- Генерирует или читает X-Request-ID, сохраняет в request.state.request_id.
- После обработки логирует: method, path, status_code, duration_ms, request_id, user_id (если есть).
- Пробрасывает request_id в заголовок ответа X-Request-ID.
"""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_STATE_KEY = "request_id"
USER_ID_STATE_KEY = "user_id"

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str:
    """Читает X-Request-ID из заголовка или генерирует новый."""
    raw = request.headers.get(REQUEST_ID_HEADER)
    if raw and raw.strip():
        return raw.strip()
    return str(uuid.uuid4())


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Добавляет request_id и логирует каждый HTTP-запрос после обработки.

    Ожидает, что request.state.user_id может быть установлен зависимостью
    (например, get_current_user) для защищённых эндпоинтов.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = _get_request_id(request)
        setattr(request.state, REQUEST_ID_STATE_KEY, request_id)
        start = time.perf_counter()

        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        status = response.status_code
        user_id = getattr(request.state, USER_ID_STATE_KEY, None)

        logger.info(
            "request_finished method=%s path=%s status=%s duration_ms=%.2f request_id=%s user_id=%s",
            request.method,
            request.url.path,
            status,
            duration_ms,
            request_id,
            user_id,
        )

        if REQUEST_ID_HEADER not in response.headers:
            response.headers[REQUEST_ID_HEADER] = request_id
        return response
