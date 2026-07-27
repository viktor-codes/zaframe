"""Studio member list and management use-cases."""

import structlog

from app.core.email_utils import normalize_email
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.observability import log_domain_event
from app.core.uow import UnitOfWork
from app.models.studio_member import StudioMember, StudioMemberRole
from app.modules.catalog.studio.member_helpers import (
    ensure_not_last_owner,
    get_member_or_raise,
    to_member_response,
)
from app.modules.catalog.studio.member_schemas import (
    StudioMemberCreate,
    StudioMemberResponse,
    StudioMemberUpdate,
)

logger = structlog.get_logger(__name__)

_ASSIGNABLE_ROLES = frozenset(
    {StudioMemberRole.MANAGER.value, StudioMemberRole.INSTRUCTOR.value}
)


async def list_studio_members(
    uow: UnitOfWork,
    *,
    studio_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[StudioMemberResponse]:
    """List members for a studio (caller must enforce manage_members)."""
    members = await uow.studio_members.list_for_studio(
        studio_id=studio_id,
        skip=skip,
        limit=limit,
    )
    return [to_member_response(member) for member in members]


async def count_studio_members(uow: UnitOfWork, *, studio_id: int) -> int:
    """Count members for pagination."""
    return await uow.studio_members.count_for_studio(studio_id=studio_id)


async def add_studio_member(
    uow: UnitOfWork,
    *,
    studio_id: int,
    schema: StudioMemberCreate,
) -> StudioMemberResponse:
    """
    Add an existing user by email as manager or instructor.

    MVP: no invite-token / pending invite — email must already belong to a user.
    """
    if schema.role not in _ASSIGNABLE_ROLES:
        raise ValidationError("Role must be manager or instructor")

    email = normalize_email(str(schema.email))
    user = await uow.users.get_by_email(email)
    if user is None:
        raise NotFoundError("User not found for this email")

    existing = await uow.studio_members.get_by_studio_and_user(
        studio_id=studio_id,
        user_id=user.id,
    )
    if existing is not None:
        raise ConflictError("User is already a member of this studio")

    created = await uow.studio_members.add(
        StudioMember(
            studio_id=studio_id,
            user_id=user.id,
            role=schema.role,
        )
    )
    member = await get_member_or_raise(uow, studio_id=studio_id, member_id=created.id)
    log_domain_event(
        logger,
        "studio_member_added",
        studio_id=studio_id,
        user_id=user.id,
        role=schema.role,
        member_id=member.id,
    )
    return to_member_response(member)


async def update_studio_member(
    uow: UnitOfWork,
    *,
    studio_id: int,
    member_id: int,
    schema: StudioMemberUpdate,
) -> StudioMemberResponse:
    """Change role to manager or instructor; block demoting the last owner."""
    if schema.role not in _ASSIGNABLE_ROLES:
        raise ValidationError("Role must be manager or instructor")

    member = await get_member_or_raise(uow, studio_id=studio_id, member_id=member_id)
    await ensure_not_last_owner(uow, member=member)

    previous_role = member.role
    if previous_role == StudioMemberRole.INSTRUCTOR.value and schema.role != previous_role:
        await uow.studio_members.clear_instructor_assignments(member_id=member.id)

    member.role = schema.role
    member = await uow.studio_members.save(member)
    member = await get_member_or_raise(uow, studio_id=studio_id, member_id=member.id)
    log_domain_event(
        logger,
        "studio_member_updated",
        studio_id=studio_id,
        member_id=member.id,
        user_id=member.user_id,
        previous_role=previous_role,
        role=schema.role,
    )
    return to_member_response(member)


async def remove_studio_member(
    uow: UnitOfWork,
    *,
    studio_id: int,
    member_id: int,
) -> None:
    """Remove a member; block removing the last owner."""
    member = await get_member_or_raise(uow, studio_id=studio_id, member_id=member_id)
    await ensure_not_last_owner(uow, member=member)
    await uow.studio_members.clear_instructor_assignments(member_id=member.id)
    user_id = member.user_id
    await uow.studio_members.delete(member)
    log_domain_event(
        logger,
        "studio_member_removed",
        studio_id=studio_id,
        member_id=member_id,
        user_id=user_id,
    )
