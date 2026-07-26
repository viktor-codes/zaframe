"use client";

import { useMemo, useState } from "react";

import {
  useStudioServicesPages,
  type ServiceResponse,
} from "@entities/service";
import { ServiceVisibility } from "@shared/lib";

export type ServiceVisibilityTab = "draft" | "published" | "archived";

/** Page size for studio services infinite list (matches bookings default). */
export const SERVICES_PAGE_SIZE = 20;

export function useStudioServices(studioId: number) {
  const [activeTab, setActiveTab] = useState<ServiceVisibilityTab>(
    ServiceVisibility.DRAFT,
  );

  const listParams = useMemo(
    () => ({ size: SERVICES_PAGE_SIZE }),
    [],
  );

  const query = useStudioServicesPages(studioId, listParams);

  const services = useMemo(
    () => (query.data?.pages ?? []).flatMap((page) => page.items),
    [query.data?.pages],
  );

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
