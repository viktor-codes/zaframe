"use client";

import { useQuery } from "@tanstack/react-query";
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

  const query = useQuery({
    queryKey: queryKeys.studio.occurrences(studioId, params),
    queryFn: () => fetchStudioOccurrences(studioId, params),
  });

  const groups = useMemo(
    () => groupOccurrencesByDate(query.data ?? []),
    [query.data],
  );

  return {
    statusFilter,
    setStatusFilter,
    params,
    groups,
    totalCount: query.data?.length ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
