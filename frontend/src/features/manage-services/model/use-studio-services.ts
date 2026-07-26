"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import type { ServiceResponse } from "@entities/service";
import { fetchStudioServices } from "@shared/api";
import { queryKeys, ServiceVisibility } from "@shared/lib";

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

  const query = useInfiniteQuery({
    queryKey: queryKeys.studio.services(studioId, listParams),
    queryFn: ({ pageParam }) =>
      fetchStudioServices(studioId, { ...listParams, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

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
