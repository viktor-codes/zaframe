from app.modules.identity.repository import UserRepository
from app.modules.identity.schemas import UserCreate, UserPublic, UserResponse, UserUpdate

__all__ = [
    "UserRepository",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserPublic",
    "get_or_create_user",
    "get_user_by_email",
    "get_user_by_id",
]


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading UserRepository from this package.
    if name in ("get_or_create_user", "get_user_by_email", "get_user_by_id"):
        from app.modules.identity.service import (
            get_or_create_user,
            get_user_by_email,
            get_user_by_id,
        )

        return {
            "get_or_create_user": get_or_create_user,
            "get_user_by_email": get_user_by_email,
            "get_user_by_id": get_user_by_id,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
