"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchOccurrenceBookings } from "@shared/api";
import { queryKeys } from "@shared/lib";

const PARTICIPANTS_PAGE_SIZE = 100;

/**
 * Participants for one occurrence (`GET /occurrences/{id}/bookings`).
 */
export function useOccurrenceParticipants(occurrenceId: number | undefined) {
  return useQuery({
    queryKey: queryKeys.occurrence.bookings(occurrenceId as number),
    queryFn: () =>
      fetchOccurrenceBookings(occurrenceId as number, {
        page: 1,
        size: PARTICIPANTS_PAGE_SIZE,
      }),
    enabled: occurrenceId != null && occurrenceId > 0,
  });
}
