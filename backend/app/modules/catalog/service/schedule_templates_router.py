"""HTTP: schedule templates nested under /services."""

from typing import Annotated

from fastapi import APIRouter, Depends

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
    get_public_or_authorized_service_or_raise,
    get_service_or_raise,
)
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

schedule_templates_router = APIRouter(prefix="/services", tags=["services"])


@schedule_templates_router.get(
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


@schedule_templates_router.post(
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


@schedule_templates_router.patch(
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


@schedule_templates_router.delete(
    "/schedule-templates/{schedule_template_id}",
    status_code=204,
)
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
