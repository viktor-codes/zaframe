"""HTTP: studio membership list and studio CRUD."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user_required, get_uow
from app.core.pagination import PaginatedResponse, paginate_all
from app.core.uow import UnitOfWork
from app.models.user import User
from app.modules.catalog.studio import (
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    StudioWithRoleResponse,
    create_studio,
    delete_studio,
    get_my_studios,
    get_studio_or_raise,
    require_studio_permission,
    update_studio,
)

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("/my", response_model=PaginatedResponse[StudioWithRoleResponse])
async def list_my_studios(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> PaginatedResponse[StudioWithRoleResponse]:
    """List studios where the current authenticated user has a membership."""
    memberships = await get_my_studios(uow, user_id=user.id)
    items = [
        StudioWithRoleResponse(
            **StudioResponse.model_validate(membership.studio).model_dump(),
            role=membership.role,
        )
        for membership in memberships
    ]
    return paginate_all(items)


@router.get("/{studio_id}", response_model=StudioResponse)
async def get_studio_by_id(
    studio_id: int,
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """Get a studio by ID."""
    studio = await get_studio_or_raise(uow, studio_id)
    return StudioResponse.model_validate(studio)


@router.post("", response_model=StudioResponse, status_code=201)
async def create_studio_endpoint(
    schema: StudioCreate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """
    Create a studio; authentication is required.

    owner_id comes from the token, and any schema-provided owner_id is ignored.
    """
    schema_with_owner = schema.model_copy(update={"owner_id": user.id})
    studio = await create_studio(uow, schema_with_owner)
    return StudioResponse.model_validate(studio)


@router.patch("/{studio_id}", response_model=StudioResponse)
async def update_studio_endpoint(
    studio_id: int,
    schema: StudioUpdate,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> StudioResponse:
    """Update a studio when the user has manage_studio permission."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_studio",
    )
    studio = await update_studio(uow, studio, schema)
    return StudioResponse.model_validate(studio)


@router.delete("/{studio_id}", status_code=204)
async def delete_studio_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> None:
    """Delete a studio when the user has manage_studio permission, including occurrences."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_studio",
    )
    await delete_studio(uow, studio)
