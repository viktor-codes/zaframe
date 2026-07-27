"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchServiceAvailability,
  type ServiceAvailabilityParams,
} from "@shared/api";
import { queryKeys } from "@shared/lib";

export interface UseCourseAvailabilityOptions {
  serviceId: number;
  /** Optional YYYY-MM-DD passed to the API; omit for backend default (today). */
  startDate?: string | null;
  enabled?: boolean;
}

/**
 * Public course availability for the book-course wizard preview.
 */
export function useCourseAvailability({
  serviceId,
  startDate = null,
  enabled = true,
}: UseCourseAvailabilityOptions) {
  const normalizedStart =
    startDate != null && startDate !== "" ? startDate : null;

  return useQuery({
    queryKey: queryKeys.service.availability(serviceId, normalizedStart),
    queryFn: ({ signal }) => {
      const params: ServiceAvailabilityParams = { signal };
      if (normalizedStart != null) {
        params.start_date = normalizedStart;
      }
      return fetchServiceAvailability(serviceId, params);
    },
    enabled: enabled && serviceId > 0,
  });
}
