"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import { fetchStudioServices } from "@shared/api";
import { queryKeys } from "@shared/lib";

import type { StudioServicesParams } from "./types";

/**
 * Paginated studio services envelope (`useInfiniteQuery`).
 * Features own tab/filter UI; this hook only owns the cache identity.
 */
export function useStudioServicesPages(
  studioId: number,
  filters: Omit<StudioServicesParams, "page"> = {},
) {
  return useInfiniteQuery({
    queryKey: queryKeys.studio.services(studioId, filters),
    queryFn: ({ pageParam }) =>
      fetchStudioServices(studioId, { ...filters, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });
}

/** Query options for `useQueries` (onboarding N+1) — keep key/fn in sync. */
export function studioServicesQueryOptions(
  studioId: number,
  params: Omit<StudioServicesParams, "page"> = {},
) {
  return {
    queryKey: queryKeys.studio.services(studioId, params),
    queryFn: () => fetchStudioServices(studioId, params),
  } as const;
}
