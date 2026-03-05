"""
Доменные исключения приложения.

Сервисы бросают только эти исключения; маппинг в HTTP (статус + body)
выполняется в одном месте — в exception handler'ах FastAPI.
Роутеры не зависят от HTTPException.
"""


class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(self, detail: str, status_code: int = 500) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppError):
    """Ресурс не найден (404)."""

    def __init__(self, detail: str = "Ресурс не найден") -> None:
        super().__init__(detail=detail, status_code=404)


class ForbiddenError(AppError):
    """Нет прав доступа (403)."""

    def __init__(self, detail: str = "Нет доступа") -> None:
        super().__init__(detail=detail, status_code=403)


class ValidationError(AppError):
    """Ошибка валидации / бизнес-правило (400)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=400)
