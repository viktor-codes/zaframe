"""Service CRUD business logic."""

from __future__ import annotations

import structlog

from app.core.exceptions import NotFoundError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models import Service, ServiceVisibility
from app.modules.catalog.service.schemas import ServiceUpdate

logger = structlog.get_logger(__name__)


async def create_service(uow: UnitOfWork, studio_id: int, data: dict[str, object]) -> Service:
    """Create a service."""
    service = Service(studio_id=studio_id, **data)
    service = await uow.services.add(service)
    log_domain_event(
        logger,
        "service_created",
        studio_id=studio_id,
        service_id=service.id,
        visibility=service.visibility,
    )
    return service


async def get_service(uow: UnitOfWork, service_id: int) -> Service | None:
    """Get service by ID."""
    return await uow.services.get_by_id(service_id)


async def get_service_or_raise(uow: UnitOfWork, service_id: int) -> Service:
    """Get service by ID or raise NotFoundError."""
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    return service


async def get_services_for_studio(
    uow: UnitOfWork,
    *,
    studio_id: int,
    skip: int = 0,
    limit: int = 20,
    is_active: bool | None = None,
) -> list[Service]:
    """List services for a studio dashboard view."""
    return await uow.services.list_by_studio(
        studio_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )


async def update_service(
    uow: UnitOfWork,
    service: Service,
    schema: ServiceUpdate,
) -> Service:
    """Update service (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    old_visibility = service.visibility
    for field, value in update_data.items():
        setattr(service, field, value)
    updated_service = await uow.services.save(service)
    log_domain_event(
        logger,
        "service_updated",
        studio_id=updated_service.studio_id,
        service_id=updated_service.id,
        updated_fields=sorted(update_data.keys()),
        old_visibility=old_visibility if old_visibility != updated_service.visibility else None,
        visibility=updated_service.visibility,
    )
    return updated_service


async def deactivate_service(uow: UnitOfWork, service: Service) -> Service:
    """Deactivate service (soft delete to preserve slots/bookings)."""
    old_visibility = service.visibility
    service.is_active = False
    service.visibility = ServiceVisibility.ARCHIVED
    service = await uow.services.save(service)
    log_domain_event(
        logger,
        "service_visibility_changed",
        studio_id=service.studio_id,
        service_id=service.id,
        old_visibility=old_visibility,
        visibility=service.visibility,
    )
    return service
