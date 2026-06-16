"""Service CRUD business logic."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.core.uow import UnitOfWork
from app.models import Service
from app.modules.catalog.service.schemas import ServiceUpdate


async def create_service(uow: UnitOfWork, studio_id: int, data: dict[str, object]) -> Service:
    """Create a service."""
    service = Service(studio_id=studio_id, **data)
    return await uow.services.add(service)


async def get_service(uow: UnitOfWork, service_id: int) -> Service | None:
    """Get service by ID."""
    return await uow.services.get_by_id(service_id)


async def get_service_or_raise(uow: UnitOfWork, service_id: int) -> Service:
    """Get service by ID or raise NotFoundError."""
    service = await uow.services.get_by_id(service_id)
    if service is None:
        raise NotFoundError("Service not found")
    return service


async def update_service(
    uow: UnitOfWork,
    service: Service,
    schema: ServiceUpdate,
) -> Service:
    """Update service (partial update)."""
    update_data = schema.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(service, field, value)
    return await uow.services.save(service)


async def deactivate_service(uow: UnitOfWork, service: Service) -> Service:
    """Deactivate service (soft delete to preserve slots/bookings)."""
    service.is_active = False
    return await uow.services.save(service)
