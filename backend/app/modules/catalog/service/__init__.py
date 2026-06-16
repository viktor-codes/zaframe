from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    CourseBookingInput,
    CourseBookingPreviewItemDTO,
    CourseBookingResultDTO,
    ServiceAvailabilityDTO,
    ServiceAvailabilityScheduleItemDTO,
)
from app.modules.catalog.service.repository import ServiceRepository
from app.modules.catalog.service.schemas import (
    ServiceAvailabilityResponse,
    ServiceAvailabilityScheduleItem,
    ServiceBase,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

__all__ = [
    "ServiceRepository",
    # Schemas
    "ServiceBase",
    "ServiceCreate",
    "ServiceUpdate",
    "ServiceResponse",
    "ServiceAvailabilityScheduleItem",
    "ServiceAvailabilityResponse",
    # DTOs
    "CourseAvailabilityDTO",
    "CourseBookingInput",
    "CourseBookingPreviewItemDTO",
    "CourseBookingResultDTO",
    "ServiceAvailabilityDTO",
    "ServiceAvailabilityScheduleItemDTO",
    # Service CRUD
    "create_service",
    "get_service",
    "get_service_or_raise",
    "update_service",
    "deactivate_service",
    # Course availability
    "check_course_availability",
    "check_course_availability_for_update",
    "get_service_availability",
    # Temporary tenant (relocate in tz-09)
    "create_course_booking",
]

_SERVICE_FUNCTIONS = (
    "create_service",
    "get_service",
    "get_service_or_raise",
    "update_service",
    "deactivate_service",
    "check_course_availability",
    "check_course_availability_for_update",
    "get_service_availability",
    "create_course_booking",
)


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading ServiceRepository from this package.
    if name in _SERVICE_FUNCTIONS:
        from app.modules.catalog.service import service

        return getattr(service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
