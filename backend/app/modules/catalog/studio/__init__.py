from app.modules.catalog.studio.repository import StudioRepository
from app.modules.catalog.studio.schemas import (
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    StudioWithOccurrences,
)

__all__ = [
    "StudioRepository",
    "StudioCreate",
    "StudioResponse",
    "StudioUpdate",
    "StudioWithOccurrences",
    "create_studio",
    "delete_studio",
    "ensure_studio_owner",
    "get_studio",
    "get_studio_or_raise",
    "get_studios",
    "get_studios_count",
    "update_studio",
]


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading StudioRepository from this package.
    if name in (
        "create_studio",
        "delete_studio",
        "ensure_studio_owner",
        "get_studio",
        "get_studio_or_raise",
        "get_studios",
        "get_studios_count",
        "update_studio",
    ):
        from app.modules.catalog.studio.service import (
            create_studio,
            delete_studio,
            ensure_studio_owner,
            get_studio,
            get_studio_or_raise,
            get_studios,
            get_studios_count,
            update_studio,
        )

        return {
            "create_studio": create_studio,
            "delete_studio": delete_studio,
            "ensure_studio_owner": ensure_studio_owner,
            "get_studio": get_studio,
            "get_studio_or_raise": get_studio_or_raise,
            "get_studios": get_studios,
            "get_studios_count": get_studios_count,
            "update_studio": update_studio,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
