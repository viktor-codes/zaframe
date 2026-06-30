import importlib
from typing import TYPE_CHECKING

from app.modules.catalog.service.dto import (
    CourseAvailabilityDTO,
    CourseBookingPreviewItemDTO,
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
    "CourseBookingPreviewItemDTO",
    "ServiceAvailabilityDTO",
    "ServiceAvailabilityScheduleItemDTO",
    # Service CRUD
    "create_service",
    "get_service",
    "get_service_or_raise",
    "get_public_or_authorized_service_or_raise",
    "get_services_for_studio",
    "update_service",
    "deactivate_service",
    # Course availability
    "check_course_availability",
    "check_course_availability_for_update",
    "get_service_availability",
]

_SERVICE_FUNCTION_MODULES: dict[str, str] = {
    "create_service": "app.modules.catalog.service.service",
    "get_service": "app.modules.catalog.service.service",
    "get_service_or_raise": "app.modules.catalog.service.service",
    "get_public_or_authorized_service_or_raise": "app.modules.catalog.service.service",
    "get_services_for_studio": "app.modules.catalog.service.service",
    "update_service": "app.modules.catalog.service.service",
    "deactivate_service": "app.modules.catalog.service.service",
    "check_course_availability": "app.modules.catalog.service.availability",
    "check_course_availability_for_update": "app.modules.catalog.service.availability",
    "get_service_availability": "app.modules.catalog.service.availability",
}

if TYPE_CHECKING:
    from app.modules.catalog.service.availability import (
        check_course_availability,
        check_course_availability_for_update,
        get_service_availability,
    )
    from app.modules.catalog.service.service import (
        create_service,
        deactivate_service,
        get_public_or_authorized_service_or_raise,
        get_service,
        get_service_or_raise,
        get_services_for_studio,
        update_service,
    )


def __getattr__(name: str):
    # WHY: service imports UnitOfWork; eager import here would cycle with core.uow
    # loading ServiceRepository from this package.
    module_path = _SERVICE_FUNCTION_MODULES.get(name)
    if module_path is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(module_path)
    return getattr(module, name)
