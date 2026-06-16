from typing import TYPE_CHECKING

from app.modules.catalog.schedule.repository import ScheduleTemplateRepository
from app.modules.catalog.schedule.schemas import (
    ScheduleGenerateRequest,
    ScheduleTemplateBase,
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
)

__all__ = [
    "ScheduleTemplateRepository",
    # Schemas
    "ScheduleTemplateBase",
    "ScheduleTemplateCreate",
    "ScheduleTemplateResponse",
    "ScheduleGenerateRequest",
    # Schedule CRUD + occurrence generation
    "create_schedule_template",
    "get_schedule_templates_for_service",
    "get_schedule_template",
    "get_schedule_template_or_raise",
    "delete_schedule_template",
    "occurrence_generator",
]

_SCHEDULE_FUNCTIONS = (
    "create_schedule_template",
    "get_schedule_templates_for_service",
    "get_schedule_template",
    "get_schedule_template_or_raise",
    "delete_schedule_template",
    "occurrence_generator",
)

if TYPE_CHECKING:
    from app.modules.catalog.schedule.service import (
        create_schedule_template,
        delete_schedule_template,
        get_schedule_template,
        get_schedule_template_or_raise,
        get_schedule_templates_for_service,
        occurrence_generator,
    )


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading ScheduleTemplateRepository from this package.
    if name in _SCHEDULE_FUNCTIONS:
        from app.modules.catalog.schedule import service

        return getattr(service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
