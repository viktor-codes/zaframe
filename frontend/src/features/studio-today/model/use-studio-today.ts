"use client";

import { useEffect, useMemo } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import { summarizeOccurrenceCapacity } from "@entities/occurrence";
import { fetchStudioOccurrences } from "@shared/api";
import { queryKeys } from "@shared/lib";

import { buildTodayParams, formatTodayHeading } from "./today-range";

export function useStudioToday(studioId: number) {
  const params = useMemo(() => buildTodayParams(), []);
  const heading = useMemo(() => formatTodayHeading(), []);

  const query = useInfiniteQuery({
    queryKey: queryKeys.studio.occurrences(studioId, params),
    queryFn: ({ pageParam }) =>
      fetchStudioOccurrences(studioId, { ...params, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

  // WHY: Today counters must cover the full local day — auto-drain pages.
  useEffect(() => {
    if (
      query.isLoading ||
      query.isFetchingNextPage ||
      !query.hasNextPage
    ) {
      return;
    }
    void query.fetchNextPage();
  }, [
    query.fetchNextPage,
    query.hasNextPage,
    query.isFetchingNextPage,
    query.isLoading,
  ]);

  const sessions = useMemo(() => {
    const items = (query.data?.pages ?? []).flatMap((page) => page.items);
    return [...items].sort((a, b) => a.start_time.localeCompare(b.start_time));
  }, [query.data?.pages]);

  const summary = useMemo(
    () => summarizeOccurrenceCapacity(sessions),
    [sessions],
  );

  return {
    heading,
    sessions,
    summary,
    totalCount: query.data?.pages[0]?.total ?? 0,
    isLoading: query.isLoading || Boolean(query.hasNextPage),
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
