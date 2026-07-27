"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchServiceScheduleTemplates } from "@shared/api";
import { queryKeys } from "@shared/lib";

export function useServiceScheduleTemplates(serviceId: number) {
  const query = useQuery({
    queryKey: queryKeys.service.scheduleTemplates(serviceId),
    queryFn: () => fetchServiceScheduleTemplates(serviceId),
  });

  return {
    templates: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
