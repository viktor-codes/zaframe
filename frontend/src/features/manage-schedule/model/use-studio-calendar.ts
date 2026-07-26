"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { groupOccurrencesByDate } from "@entities/occurrence";
import { fetchStudioOccurrences } from "@shared/api";
import { queryKeys } from "@shared/lib";

import {
  buildCalendarParams,
  type CalendarStatusFilter,
} from "./calendar-range";

export function useStudioCalendar(studioId: number) {
  const [statusFilter, setStatusFilter] =
    useState<CalendarStatusFilter>("scheduled");

  const params = useMemo(
    () => buildCalendarParams(statusFilter),
    [statusFilter],
  );

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

  const occurrences = useMemo(
    () => (query.data?.pages ?? []).flatMap((page) => page.items),
    [query.data?.pages],
  );

  const groups = useMemo(
    () => groupOccurrencesByDate(occurrences),
    [occurrences],
  );

  return {
    statusFilter,
    setStatusFilter,
    params,
    groups,
    totalCount: query.data?.pages[0]?.total ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
    fetchNextPage: query.fetchNextPage,
    hasNextPage: Boolean(query.hasNextPage),
    isFetchingNextPage: query.isFetchingNextPage,
  };
}
