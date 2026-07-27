"use client";

import { useMemo, useState } from "react";

import {
  groupOccurrencesByDate,
  useStudioOccurrencesPages,
} from "@entities/occurrence";

import { OccurrenceStatus } from "@shared/lib";

import {
  buildCalendarParams,
  type CalendarStatusFilter,
} from "./calendar-range";

export function useStudioCalendar(studioId: number) {
  const [statusFilter, setStatusFilter] = useState<CalendarStatusFilter>(
    OccurrenceStatus.SCHEDULED,
  );

  const params = useMemo(
    () => buildCalendarParams(statusFilter),
    [statusFilter],
  );

  const query = useStudioOccurrencesPages(studioId, params);

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
