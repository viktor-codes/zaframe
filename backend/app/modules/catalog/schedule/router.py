"""HTTP routes for schedule generation (studio owner)."""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.occurrence import OccurrenceResponse
from app.modules.catalog.schedule import ScheduleGenerateRequest, occurrence_generator
from app.modules.catalog.studio import ensure_studio_owner, get_studio_or_raise

schedule_router = APIRouter(prefix="/studios", tags=["studios"])


@schedule_router.post("/{studio_id}/generate-occurrences", response_model=list[OccurrenceResponse])
async def generate_studio_occurrences_endpoint(
    studio_id: int,
    schema: ScheduleGenerateRequest,
    user: User = Depends(get_current_user_required),
    uow: UnitOfWork = Depends(get_uow),
) -> list[OccurrenceResponse]:
    """
    Сгенерировать расписание для услуги в студии.

    Создаёт слоты на указанные дни недели в течение `weeks_count` недель.
    """
    studio = await get_studio_or_raise(uow, studio_id)
    ensure_studio_owner(studio, user.id)

    occurrences = await occurrence_generator(
        uow,
        studio_id=studio_id,
        service_id=schema.service_id,
        days=schema.days,
        start_time=schema.start_time,
        weeks_count=schema.weeks_count,
    )
    return [OccurrenceResponse.model_validate(o) for o in occurrences]
