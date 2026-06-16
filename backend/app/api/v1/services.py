"""
API роутер для услуг (Service) и шаблонов расписания (ScheduleTemplate).

Операции:
- CRUD для Service
- Список и создание ScheduleTemplate для услуги
"""

from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user_required, get_uow
from app.api.mappers.service import map_service_availability
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.schedule import (
    create_schedule_template,
    delete_schedule_template,
    get_schedule_template_or_raise,
    get_schedule_templates_for_service,
)
from app.modules.catalog.service import (
    create_service,
    deactivate_service,
    get_service_availability,
    get_service_or_raise,
    update_service,
)
from app.modules.catalog.studio import ensure_studio_owner, get_studio_or_raise
from app.schemas import (
    ScheduleTemplateBase,
    ScheduleTemplateCreate,
    ScheduleTemplateResponse,
    ServiceAvailabilityResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service_endpoint(
    schema: ServiceCreate,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> ServiceResponse:
    """
    Создать услугу (Service) в студии.

    Требуется аутентификация и владение студией.
    """
    studio = await get_studio_or_raise(uow, schema.studio_id)
    ensure_studio_owner(studio, user.id)

    data = schema.model_dump(exclude={"studio_id"})
    service = await create_service(uow, schema.studio_id, data)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_endpoint(
    service_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> ServiceResponse:
    """Получить услугу по ID (публично)."""
    service = await get_service_or_raise(uow, service_id)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}/availability", response_model=ServiceAvailabilityResponse)
async def get_service_availability_endpoint(
    service_id: int,
    start_date: date | None = Query(
        None,
        description="Опциональная дата, с которой считать доступность (по умолчанию сегодня)",
    ),
    uow: UnitOfWork = Depends(get_uow),
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
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> ServiceResponse:
    """Обновить услугу (только владелец студии)."""
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)
    service = await update_service(uow, service, schema)
    return ServiceResponse.model_validate(service)


@router.delete("/{service_id}", response_model=ServiceResponse)
async def deactivate_service_endpoint(
    service_id: int,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> ServiceResponse:
    """
    Деактивировать услугу (soft delete).

    Связанные occurrence'ы и бронирования остаются в системе.
    """
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)
    service = await deactivate_service(uow, service)
    return ServiceResponse.model_validate(service)


@router.get(
    "/{service_id}/schedule-templates",
    response_model=list[ScheduleTemplateResponse],
)
async def list_service_schedule_templates_endpoint(
    service_id: int,
    uow: UnitOfWork = Depends(get_uow),
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
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> ScheduleTemplateResponse:
    """
    Создать шаблон расписания (ScheduleTemplate) для услуги.
    """
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)

    schedule_schema = ScheduleTemplateCreate(
        service_id=service_id,
        **schema.model_dump(),
    )
    schedule = await create_schedule_template(uow, schedule_schema)
    return ScheduleTemplateResponse.model_validate(schedule)


@router.delete("/schedule-templates/{schedule_template_id}", status_code=204)
async def delete_schedule_template_endpoint(
    schedule_template_id: int,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Удалить шаблон расписания (только владелец студии услуги)."""
    schedule = await get_schedule_template_or_raise(uow, schedule_template_id)
    service = await get_service_or_raise(uow, schedule.service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_schedule_template(uow, schedule)
