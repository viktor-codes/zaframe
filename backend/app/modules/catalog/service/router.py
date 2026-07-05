"""
Service and ScheduleTemplate API router.

Operations:
- Service CRUD
- List and create ScheduleTemplate rows for a service
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, paginate_all
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.schedule import (
    ScheduleTemplateBase,
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
    ScheduleTemplateUpdate,
    create_schedule_template,
    delete_schedule_template,
    get_schedule_template_or_raise,
    get_schedule_templates_for_service,
    update_schedule_template,
)
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


@router.get(
    "/{service_id}/schedule-templates",
    response_model=PaginatedResponse[ScheduleTemplateResponse],
)
async def list_service_schedule_templates_endpoint(
    service_id: int,
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> PaginatedResponse[ScheduleTemplateResponse]:
    """List schedule templates for a service."""
    await get_public_or_authorized_service_or_raise(uow, service_id, user=user)
    schedules = await get_schedule_templates_for_service(uow, service_id=service_id)
    items = [ScheduleTemplateResponse.model_validate(schedule) for schedule in schedules]
    return paginate_all(items)


@router.post(
    "/{service_id}/schedule-templates",
    response_model=ScheduleTemplateResponse,
    status_code=201,
)
async def create_service_schedule_template_endpoint(
    service_id: int,
    schema: ScheduleTemplateBase,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ScheduleTemplateResponse:
    """Create a schedule template for a service."""
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )

    schedule_schema = ScheduleTemplateCreate(
        service_id=service_id,
        **schema.model_dump(),
    )
    schedule = await create_schedule_template(uow, schedule_schema)
    return ScheduleTemplateResponse.model_validate(schedule)


@router.patch(
    "/schedule-templates/{schedule_template_id}",
    response_model=ScheduleTemplateResponse,
)
async def update_schedule_template_endpoint(
    schedule_template_id: int,
    schema: ScheduleTemplateUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ScheduleTemplateResponse:
    """
    Update a schedule template.

    Existing generated occurrences are intentionally preserved; owners must edit
    or cancel generated occurrences explicitly.
    """
    schedule = await get_schedule_template_or_raise(uow, schedule_template_id)
    service = await get_service_or_raise(uow, schedule.service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )
    updated = await update_schedule_template(uow, schedule, schema)
    return ScheduleTemplateResponse.model_validate(updated)


@router.delete("/schedule-templates/{schedule_template_id}", status_code=204)
async def delete_schedule_template_endpoint(
    schedule_template_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Delete a schedule template when the user has manage_schedule permission."""
    schedule = await get_schedule_template_or_raise(uow, schedule_template_id)
    service = await get_service_or_raise(uow, schedule.service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )
    await delete_schedule_template(uow, schedule)
