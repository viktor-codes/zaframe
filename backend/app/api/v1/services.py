"""
API роутер для услуг (Service) и шаблонов расписания (Schedule).

Операции:
- CRUD для Service
- Список и создание Schedule для услуги
"""
from fastapi import APIRouter, Depends, Query

from datetime import date

from app.api.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.schemas import (
    ScheduleBase,
    ScheduleCreate,
    ScheduleResponse,
    ServiceAvailabilityResponse,
    ServiceCreate,
    ServiceResponse,
    ServiceUpdate,
)
from app.services.service import (
    create_schedule,
    create_service,
    deactivate_service,
    delete_schedule,
    get_schedule_or_raise,
    get_schedules_for_service,
    get_service_or_raise,
    get_service_availability,
    update_service,
)
from app.services.studio import ensure_studio_owner, get_studio_or_raise

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
    return await get_service_availability(uow, service_id=service_id, start_date=start_date)


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

    Связанные слоты и бронирования остаются в системе.
    """
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)
    service = await deactivate_service(uow, service)
    return ServiceResponse.model_validate(service)


@router.get(
    "/{service_id}/schedules",
    response_model=list[ScheduleResponse],
)
async def list_service_schedules_endpoint(
    service_id: int,
    uow: UnitOfWork = Depends(get_uow),
) -> list[ScheduleResponse]:
    """Список шаблонов расписания для услуги."""
    await get_service_or_raise(uow, service_id)
    schedules = await get_schedules_for_service(uow, service_id=service_id)
    return [ScheduleResponse.model_validate(s) for s in schedules]


@router.post(
    "/{service_id}/schedules",
    response_model=ScheduleResponse,
    status_code=201,
)
async def create_service_schedule_endpoint(
    service_id: int,
    schema: ScheduleBase,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> ScheduleResponse:
    """
    Создать шаблон расписания (Schedule) для услуги.
    """
    service = await get_service_or_raise(uow, service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)

    schedule_schema = ScheduleCreate(
        service_id=service_id,
        **schema.model_dump(),
    )
    schedule = await create_schedule(uow, schedule_schema)
    return ScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule_endpoint(
    schedule_id: int,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> None:
    """Удалить шаблон расписания (только владелец студии услуги)."""
    schedule = await get_schedule_or_raise(uow, schedule_id)
    service = await get_service_or_raise(uow, schedule.service_id)
    studio = await get_studio_or_raise(uow, service.studio_id)
    ensure_studio_owner(studio, user.id)
    await delete_schedule(uow, schedule)

