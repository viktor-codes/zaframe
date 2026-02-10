"""
API роутер для услуг (Service) и шаблонов расписания (Schedule).

Операции:
- CRUD для Service
- Список и создание Schedule для услуги
"""
from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_required, get_db
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
    get_schedule,
    get_schedules_for_service,
    get_service,
    get_service_availability,
    update_service,
)
from app.services.studio import get_studio

router = APIRouter(prefix="/services", tags=["services"])


def _ensure_service_owner(service, studio, user: User) -> None:
    """Проверка, что пользователь является владельцем студии услуги."""
    if studio is None or studio.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой услуге")


@router.post("", response_model=ServiceResponse, status_code=201)
async def create_service_endpoint(
    schema: ServiceCreate,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> ServiceResponse:
    """
    Создать услугу (Service) в студии.

    Требуется аутентификация и владение студией.
    """
    studio = await get_studio(db, schema.studio_id)
    if studio is None:
        raise HTTPException(status_code=404, detail="Студия не найдена")
    if studio.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Нет доступа к этой студии")

    data = schema.model_dump(exclude={"studio_id"})
    service = await create_service(db, schema.studio_id, data)
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}", response_model=ServiceResponse)
async def get_service_endpoint(
    service_id: int,
    db: AsyncSession = Depends(get_db),
) -> ServiceResponse:
    """Получить услугу по ID (публично)."""
    service = await get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    return ServiceResponse.model_validate(service)


@router.get("/{service_id}/availability", response_model=ServiceAvailabilityResponse)
async def get_service_availability_endpoint(
    service_id: int,
    start_date: date | None = Query(
        None,
        description="Опциональная дата, с которой считать доступность (по умолчанию сегодня)",
    ),
    db: AsyncSession = Depends(get_db),
) -> ServiceAvailabilityResponse:
    """
    Получить подробную информацию о доступности курса.

    Используется фронтендом при открытии модалки покупки, чтобы
    показать календарь занятости.
    """
    return await get_service_availability(db, service_id=service_id, start_date=start_date)


@router.patch("/{service_id}", response_model=ServiceResponse)
async def update_service_endpoint(
    service_id: int,
    schema: ServiceUpdate,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> ServiceResponse:
    """Обновить услугу (только владелец студии)."""
    service = await get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    studio = await get_studio(db, service.studio_id)
    _ensure_service_owner(service, studio, user)
    service = await update_service(db, service, schema)
    return ServiceResponse.model_validate(service)


@router.delete("/{service_id}", response_model=ServiceResponse)
async def deactivate_service_endpoint(
    service_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> ServiceResponse:
    """
    Деактивировать услугу (soft delete).

    Связанные слоты и бронирования остаются в системе.
    """
    service = await get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    studio = await get_studio(db, service.studio_id)
    _ensure_service_owner(service, studio, user)
    service = await deactivate_service(db, service)
    return ServiceResponse.model_validate(service)


@router.get(
    "/{service_id}/schedules",
    response_model=list[ScheduleResponse],
)
async def list_service_schedules_endpoint(
    service_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ScheduleResponse]:
    """Список шаблонов расписания для услуги."""
    service = await get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    schedules = await get_schedules_for_service(db, service_id=service_id)
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
    db: AsyncSession = Depends(get_db),
) -> ScheduleResponse:
    """
    Создать шаблон расписания (Schedule) для услуги.
    """
    service = await get_service(db, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    studio = await get_studio(db, service.studio_id)
    _ensure_service_owner(service, studio, user)

    schedule_schema = ScheduleCreate(
        service_id=service_id,
        **schema.model_dump(),
    )
    schedule = await create_schedule(db, schedule_schema)
    return ScheduleResponse.model_validate(schedule)


@router.delete("/schedules/{schedule_id}", status_code=204)
async def delete_schedule_endpoint(
    schedule_id: int,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Удалить шаблон расписания (только владелец студии услуги)."""
    schedule = await get_schedule(db, schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="Расписание не найдено")
    service = await get_service(db, schedule.service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Услуга не найдена")
    studio = await get_studio(db, service.studio_id)
    _ensure_service_owner(service, studio, user)
    await delete_schedule(db, schedule)

