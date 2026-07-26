"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import type { ServiceResponse } from "@entities/service";
import { fetchStudioServices } from "@shared/api";
import { queryKeys, ServiceVisibility } from "@shared/lib";

export type ServiceVisibilityTab = "draft" | "published" | "archived";

export function useStudioServices(studioId: number) {
  const [activeTab, setActiveTab] = useState<ServiceVisibilityTab>(
    ServiceVisibility.DRAFT,
  );

  const query = useQuery({
    queryKey: queryKeys.studio.services(studioId),
    queryFn: () => fetchStudioServices(studioId),
  });

  const services = query.data ?? [];

  const counts = useMemo(() => {
    const next = {
      draft: 0,
      published: 0,
      archived: 0,
    };
    for (const service of services) {
      if (service.visibility in next) {
        next[service.visibility as ServiceVisibilityTab] += 1;
      }
    }
    return next;
  }, [services]);

  const tabServices = useMemo(
    () =>
      services.filter(
        (service: ServiceResponse) => service.visibility === activeTab,
      ),
    [activeTab, services],
  );

  return {
    activeTab,
    setActiveTab,
    counts,
    tabServices,
    totalCount: services.length,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
