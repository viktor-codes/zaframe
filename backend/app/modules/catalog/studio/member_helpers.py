"""Internal helpers for studio member responses and owner-safety checks."""

from app.core.exceptions import ConflictError, NotFoundError
from app.core.uow import UnitOfWork
from app.models.studio_member import StudioMember, StudioMemberRole
from app.modules.catalog.studio.member_schemas import StudioMemberResponse


def to_member_response(member: StudioMember) -> StudioMemberResponse:
    user = member.user
    return StudioMemberResponse(
        id=member.id,
        studio_id=member.studio_id,
        user_id=member.user_id,
        role=member.role,
        email=user.email,
        name=user.name,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


async def get_member_or_raise(
    uow: UnitOfWork,
    *,
    studio_id: int,
    member_id: int,
) -> StudioMember:
    member = await uow.studio_members.get_by_id_with_user(member_id)
    if member is None or member.studio_id != studio_id:
        raise NotFoundError("Studio member not found")
    return member


async def ensure_not_last_owner(uow: UnitOfWork, *, member: StudioMember) -> None:
    if member.role != StudioMemberRole.OWNER.value:
        return
    owner_count = await uow.studio_members.count_owners(studio_id=member.studio_id)
    if owner_count <= 1:
        raise ConflictError("Cannot modify or remove the last studio owner")
