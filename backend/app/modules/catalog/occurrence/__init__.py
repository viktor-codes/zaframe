from app.modules.catalog.occurrence.repository import OccurrenceRepository
from app.modules.catalog.occurrence.schemas import (
    OccurrenceCreate,
    OccurrenceResponse,
    OccurrenceUpdate,
    OccurrenceWithBookings,
)

__all__ = [
    "OccurrenceRepository",
    "OccurrenceCreate",
    "OccurrenceResponse",
    "OccurrenceUpdate",
    "OccurrenceWithBookings",
    "create_occurrence",
    "delete_occurrence",
    "get_occurrence",
    "get_occurrence_or_raise",
    "get_occurrences",
    "get_occurrences_count",
    "update_occurrence",
]


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading OccurrenceRepository from this package.
    if name in (
        "create_occurrence",
        "delete_occurrence",
        "get_occurrence",
        "get_occurrence_or_raise",
        "get_occurrences",
        "get_occurrences_count",
        "update_occurrence",
    ):
        from app.modules.catalog.occurrence.service import (
            create_occurrence,
            delete_occurrence,
            get_occurrence,
            get_occurrence_or_raise,
            get_occurrences,
            get_occurrences_count,
            update_occurrence,
        )

        return {
            "create_occurrence": create_occurrence,
            "delete_occurrence": delete_occurrence,
            "get_occurrence": get_occurrence,
            "get_occurrence_or_raise": get_occurrence_or_raise,
            "get_occurrences": get_occurrences,
            "get_occurrences_count": get_occurrences_count,
            "update_occurrence": update_occurrence,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
