"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudioMembers } from "@shared/api";
import { queryKeys } from "@shared/lib";

/**
 * Studio team list (`GET /studios/{id}/members`, requires manage_members).
 */
export function useStudioMembers(studioId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.studio.members(studioId as number),
    queryFn: () => fetchStudioMembers(studioId as number),
    enabled: studioId != null && studioId > 0,
  });
}
