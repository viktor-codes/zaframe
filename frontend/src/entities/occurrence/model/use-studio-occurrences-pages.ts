"use client";

import { useInfiniteQuery } from "@tanstack/react-query";

import {
  fetchStudioOccurrences,
  type StudioOccurrencesParams,
} from "@shared/api";
import { queryKeys } from "@shared/lib";

/**
 * Paginated studio occurrences envelope (`useInfiniteQuery`).
 * Features own date/status UI; this hook only owns the cache identity.
 */
export function useStudioOccurrencesPages(
  studioId: number,
  filters: Omit<StudioOccurrencesParams, "page"> = {},
) {
  return useInfiniteQuery({
    queryKey: queryKeys.studio.occurrences(studioId, filters),
    queryFn: ({ pageParam }) =>
      fetchStudioOccurrences(studioId, { ...filters, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });
}
