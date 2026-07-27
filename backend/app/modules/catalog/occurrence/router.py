"""HTTP: occurrence CRUD (get / create / update / delete)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user_required, get_uow
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.occurrence import (
    OccurrenceCreate,
    OccurrenceResponse,
    OccurrenceUpdate,
    create_occurrence,
    delete_occurrence,
    get_occurrence_or_raise,
    update_occurrence,
)
from app.modules.catalog.studio import get_studio_or_raise, require_studio_permission

router = APIRouter(prefix="/occurrences", tags=["occurrences"])


@router.get("/{occurrence_id}", response_model=OccurrenceResponse)
async def get_occurrence_by_id(
    occurrence_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Get occurrence by ID."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    return OccurrenceResponse.model_validate(occurrence)


@router.post("", response_model=OccurrenceResponse, status_code=201)
async def create_occurrence_endpoint(
    schema: OccurrenceCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Create occurrence (studio owner)."""
    studio = await get_studio_or_raise(uow, schema.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )
    occurrence = await create_occurrence(uow, schema)
    occurrence = await get_occurrence_or_raise(uow, occurrence.id)
    return OccurrenceResponse.model_validate(occurrence)


@router.patch("/{occurrence_id}", response_model=OccurrenceResponse)
async def update_occurrence_endpoint(
    occurrence_id: int,
    schema: OccurrenceUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> OccurrenceResponse:
    """Update occurrence (studio owner)."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    studio = await get_studio_or_raise(uow, occurrence.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )
    occurrence = await update_occurrence(uow, occurrence, schema)
    occurrence = await get_occurrence_or_raise(uow, occurrence.id)
    return OccurrenceResponse.model_validate(occurrence)


@router.delete("/{occurrence_id}", status_code=204)
async def delete_occurrence_endpoint(
    occurrence_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Delete occurrence (studio owner). Cascades to related bookings."""
    occurrence = await get_occurrence_or_raise(uow, occurrence_id)
    studio = await get_studio_or_raise(uow, occurrence.studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_schedule",
    )
    await delete_occurrence(uow, occurrence)
