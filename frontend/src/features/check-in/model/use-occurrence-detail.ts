"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchOccurrence } from "@shared/api";
import { queryKeys } from "@shared/lib";

/**
 * Occurrence detail for the check-in header.
 */
export function useOccurrenceDetail(occurrenceId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.occurrence.detail(occurrenceId),
    queryFn: () => fetchOccurrence(occurrenceId as number),
    enabled: occurrenceId != null && occurrenceId > 0,
  });
}
