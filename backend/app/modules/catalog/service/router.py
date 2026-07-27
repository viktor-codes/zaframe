"""HTTP: service CRUD and course availability."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.service import (
    ServiceAvailabilityResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
    create_service,
    deactivate_service,
    get_public_or_authorized_service_or_raise,
    get_service_availability,
    get_service_or_raise,
    update_service,
)
from app.modules.catalog.service.mappers import map_service_availability
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service_endpoint(
    schema: ServiceCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ServiceResponse:
    """
    Create a service in a studio.

    Requires authentication and permission to manage studio services.
    """
    studio = await get_studio_or_raise(uow, schema.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_services",
    )

    data = schema.model_dump(exclude={"studio_id"})
    service = await create_service(uow, schema.studio_id, data)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_endpoint(
    service_id: int,
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ServiceResponse:
    """Get a public service by ID, or any lifecycle state for studio managers."""
    service = await get_public_or_authorized_service_or_raise(uow, service_id, user=user)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}/availability", response_model=ServiceAvailabilityResponse)
async def get_service_availability_endpoint(
    service_id: int,
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    start_date: date | None = Query(
        None,
        description="Optional date to start availability calculation from; defaults to today",
    ),
) -> ServiceAvailabilityResponse:
    """
    Get detailed course availability information.

    Used by the frontend purchase modal to show the occupancy calendar.
    """
    await get_public_or_authorized_service_or_raise(uow, service_id, user=user)
    return map_service_availability(
        await get_service_availability(uow, service_id=service_id, start_date=start_date),
    )


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service_endpoint(
    service_id: int,
    schema: ServiceUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ServiceResponse:
    """Update a service when the user has manage_services permission."""
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_services",
    )
    service = await update_service(uow, service, schema)
    return ServiceResponse.model_validate(service)


@router.delete("/{service_id}", response_model=ServiceResponse)
async def deactivate_service_endpoint(
    service_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ServiceResponse:
    """
    Deactivate a service as a soft delete.

    Related occurrences and bookings remain in the system.
    """
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_services",
    )
    service = await deactivate_service(uow, service)
    return ServiceResponse.model_validate(service)
