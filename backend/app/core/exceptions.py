"""
Domain exceptions for the application.

Services raise only these exceptions; mapping to HTTP (status + body) is done
in one place — FastAPI exception handlers. Routers do not use HTTPException.
"""


class AppError(Exception):
    """Base application exception."""

    def __init__(self, detail: str, status_code: int = 500) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppError):
    """Resource not found (404)."""

    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail=detail, status_code=404)


class ForbiddenError(AppError):
    """Insufficient permissions (403)."""

    def __init__(self, detail: str = "Access denied") -> None:
        super().__init__(detail=detail, status_code=403)


class ValidationError(AppError):
    """Validation or business rule failure (400)."""

    def __init__(self, detail: str) -> None:
        super().__init__(detail=detail, status_code=400)


class UnauthorizedError(AppError):
    """Authentication required or invalid credentials (401)."""

    def __init__(self, detail: str = "Authentication required") -> None:
        super().__init__(detail=detail, status_code=401)
