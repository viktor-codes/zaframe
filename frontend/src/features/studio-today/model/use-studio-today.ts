"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { summarizeOccurrenceCapacity } from "@entities/occurrence";
import { fetchStudioOccurrences } from "@shared/api";
import { queryKeys } from "@shared/lib";

import { buildTodayParams, formatTodayHeading } from "./today-range";

export function useStudioToday(studioId: number) {
  const params = useMemo(() => buildTodayParams(), []);
  const heading = useMemo(() => formatTodayHeading(), []);

  const query = useQuery({
    queryKey: queryKeys.studio.occurrences(studioId, params),
    queryFn: () => fetchStudioOccurrences(studioId, params),
  });

  const sessions = useMemo(() => {
    const items = query.data ?? [];
    return [...items].sort((a, b) => a.start_time.localeCompare(b.start_time));
  }, [query.data]);

  const summary = useMemo(
    () => summarizeOccurrenceCapacity(sessions),
    [sessions],
  );

  return {
    heading,
    sessions,
    summary,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
