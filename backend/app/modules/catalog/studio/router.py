"""
Studio API router.

CRUD operations:
- GET /studios - paginated list
- GET /studios/{id} - one studio
- POST /studios - create
- PATCH /studios/{id} - update
- DELETE /studios/{id} - delete

Why the router is separated:
- Thin layer for HTTP concerns, validation, and service calls
- Matches the structure defined in .cursorrules
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.deps import get_current_user, get_current_user_required, get_uow
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.uow import UnitOfWork
from app.models.service import ServiceCategory
from app.models.user import User
from app.modules.catalog.service import ServiceResponse, get_services_for_studio
from app.modules.catalog.studio import (
    StudioCreate,
    StudioResponse,
    StudioUpdate,
    StudioWithRoleResponse,
    create_studio,
    delete_studio,
    get_my_studios,
    get_studio_or_raise,
    get_studios,
    get_studios_count,
    require_studio_permission,
    update_studio,
)
from app.modules.catalog.studio.explore import attach_services_to_studios

router = APIRouter(prefix="/studios", tags=["studios"])


@router.get("")
async def list_studios(
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    owner_id: int | None = Query(None, description="Filter by owner for owner dashboards"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    city: str | None = Query(None, description="Explore city filter"),
    category: ServiceCategory | None = Query(None, description="Explore service category filter"),
    query: str | None = Query(None, description="Explore studio/service name search"),
    amenities: list[str] | None = Query(None, description="Explore amenities filter"),
    include_services: bool = Query(False, description="Return card services with price/category"),
):
    """
    List studios with pagination and optional Explore filters.

    When include_services=true, returns list[SearchResult] (studio + services);
    otherwise returns list[StudioResponse].
    """
    if owner_id is not None:
        if user is None:
            raise UnauthorizedError("Authentication required")
        if owner_id != user.id:
            raise ForbiddenError("Access denied for this owner filter")
    studios = await get_studios(
        uow,
        skip=skip,
        limit=limit,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    if not include_services:
        return [StudioResponse.model_validate(s) for s in studios]

    return await attach_services_to_studios(
        uow,
        studios,
        category=category.value if category is not None else None,
    )


@router.get("/my", response_model=list[StudioWithRoleResponse])
async def list_my_studios(
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
) -> list[StudioWithRoleResponse]:
    """List studios where the current authenticated user has a membership."""
    memberships = await get_my_studios(uow, user_id=user.id)
    return [
        StudioWithRoleResponse(
            **StudioResponse.model_validate(membership.studio).model_dump(),
            role=membership.role,
        )
        for membership in memberships
    ]


@router.get("/count")
async def count_studios(
    user: Annotated[User | None, Depends(get_current_user)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    owner_id: int | None = Query(None, description="Filter by owner"),
    is_active: bool | None = Query(None, description="Filter by active status"),
    city: str | None = Query(None, description="Explore city filter"),
    category: ServiceCategory | None = Query(None, description="Explore service category filter"),
    query: str | None = Query(None, description="Explore name search"),
    amenities: list[str] | None = Query(None, description="Explore amenities filter"),
) -> dict[str, int]:
    """Count studios for pagination using the same filters as list."""
    if owner_id is not None:
        if user is None:
            raise UnauthorizedError("Authentication required")
        if owner_id != user.id:
            raise ForbiddenError("Access denied for this owner filter")
    count = await get_studios_count(
        uow,
        owner_id=owner_id,
        is_active=is_active,
        city=city,
        category=category.value if category is not None else None,
        query=query,
        amenities=amenities,
    )
    return {"count": count}


@router.get("/{studio_id}/services", response_model=list[ServiceResponse])
async def list_studio_services_endpoint(
    studio_id: int,
    user: Annotated[User, Depends(get_current_user_required)],
    uow: Annotated[UnitOfWork, Depends(get_uow)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records"),
    is_active: bool | None = Query(None, description="Filter by service active status"),
) -> list[ServiceResponse]:
    """List services for a studio dashboard with service-management permission."""
    studio = await get_studio_or_raise(uow, studio_id)
    await require_studio_permission(
        uow,
        studio=studio,
        user=user,
        permission="manage_services",
    )
    services = await get_services_for_studio(
        uow,
        studio_id=studio_id,
        skip=skip,
        limit=limit,
        is_active=is_active,
    )
    return [ServiceResponse.model_validate(service) for service in services]


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
