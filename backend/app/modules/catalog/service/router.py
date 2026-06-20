from typing import Annotated

"""
API роутер для услуг (Service) и шаблонов расписания (ScheduleTemplate).

Операции:
- CRUD для Service
- Список и создание ScheduleTemplate для услуги
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user_required, get_uow
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
    Создать услугу (Service) в студии.

    Требуется аутентификация и право управлять услугами студии.
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
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> ServiceResponse:
    """Получить услугу по ID (публично)."""
    service = await get_service_or_raise(uow, service_id)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}/availability", response_model=ServiceAvailabilityResponse)
async def get_service_availability_endpoint(
    service_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    start_date: date | None = Query(
        None,
        description="Опциональная дата, с которой считать доступность (по умолчанию сегодня)",
    ),
) -> ServiceAvailabilityResponse:
    """
    Получить подробную информацию о доступности курса.

    Используется фронтендом при открытии модалки покупки, чтобы
    показать календарь занятости.
    """
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
    """Обновить услугу при наличии права manage_services."""
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
    Деактивировать услугу (soft delete).

    Связанные occurrence'ы и бронирования остаются в системе.
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
    response_model=list[ScheduleTemplateResponse],
)
async def list_service_schedule_templates_endpoint(
    service_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[ScheduleTemplateResponse]:
    """Список шаблонов расписания для услуги."""
    await get_service_or_raise(uow, service_id)
    schedules = await get_schedule_templates_for_service(uow, service_id=service_id)
    return [ScheduleTemplateResponse.model_validate(s) for s in schedules]


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
    """
    Создать шаблон расписания (ScheduleTemplate) для услуги.
    """
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
    """Удалить шаблон расписания при наличии права manage_schedule."""
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
