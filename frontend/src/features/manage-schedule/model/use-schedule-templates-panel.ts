"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchService } from "@shared/api";
import { queryKeys } from "@shared/lib";

import { useServiceScheduleTemplates } from "./use-service-schedule-templates";

export function useScheduleTemplatesPanel(
  studioId: number,
  serviceId: number,
) {
  const serviceQuery = useQuery({
    queryKey: queryKeys.service.detail(serviceId),
    queryFn: () => fetchService(serviceId),
  });

  const templatesQuery = useServiceScheduleTemplates(serviceId);

  const isLoading = serviceQuery.isLoading || templatesQuery.isLoading;
  const service = serviceQuery.data;
  const isWrongStudio =
    service != null && service.studio_id !== studioId;

  return {
    isLoading,
    service,
    serviceError: serviceQuery.error,
    refetchService: serviceQuery.refetch,
    isServiceError: serviceQuery.isError || !service,
    isWrongStudio,
    templates: templatesQuery.templates,
    isTemplatesError: templatesQuery.isError,
    templatesError: templatesQuery.error,
    refetchTemplates: templatesQuery.refetch,
  };
}
