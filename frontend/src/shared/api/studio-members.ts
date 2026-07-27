/**
 * Studio members API (`manage_members` — owner-only in the permission matrix).
 *
 * MVP: add by email of an existing user (no pending-invite flow).
 */

import type {
  PaginatedStudioMemberList,
  StudioMemberCreate,
  StudioMemberResponse,
  StudioMemberUpdate,
  StudioMembersParams,
} from "@entities/studio";

import { api } from "./client";

export type { StudioMembersParams };

const DEFAULT_PAGE = 1;
const DEFAULT_MEMBER_PAGE_SIZE = 20;

/**
 * Studio members list envelope (`{ items, total, page, size }`).
 * Callers must use `total` — never treat `items.length` as the full count.
 */
export async function fetchStudioMembers(
  studioId: number,
  params: StudioMembersParams = {},
): Promise<PaginatedStudioMemberList> {
  const searchParams: Record<string, string | number | boolean | undefined> = {
    page: params.page ?? DEFAULT_PAGE,
    size: params.size ?? DEFAULT_MEMBER_PAGE_SIZE,
  };

  return api.get<PaginatedStudioMemberList>(
    `api/v1/studios/${studioId}/members`,
    {
      params: searchParams,
    },
  );
}

/** Add an existing user by email as manager or instructor. */
export async function addStudioMember(
  studioId: number,
  data: StudioMemberCreate,
): Promise<StudioMemberResponse> {
  return api.post<StudioMemberResponse>(
    `api/v1/studios/${studioId}/members`,
    data,
  );
}

/** Change role to manager or instructor (cannot demote the last owner). */
export async function updateStudioMember(
  studioId: number,
  memberId: number,
  data: StudioMemberUpdate,
): Promise<StudioMemberResponse> {
  return api.patch<StudioMemberResponse>(
    `api/v1/studios/${studioId}/members/${memberId}`,
    data,
  );
}

/** Remove a member (cannot remove the last owner). */
export async function removeStudioMember(
  studioId: number,
  memberId: number,
): Promise<void> {
  return api.delete<void>(`api/v1/studios/${studioId}/members/${memberId}`);
}
