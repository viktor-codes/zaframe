"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchStudio } from "@shared/api";
import { queryKeys } from "@shared/lib";

/**
 * Studio detail by id (`GET /studios/{id}`).
 * Used by dashboard profile and legacy public redirects.
 */
export function useStudio(studioId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.studio.detail(studioId),
    queryFn: () => fetchStudio(studioId as number),
    enabled: studioId != null && studioId > 0,
  });
}
