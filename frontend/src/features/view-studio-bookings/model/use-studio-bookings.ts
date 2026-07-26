"use client";

import { useMemo, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";

import type { BookingWithOccurrence } from "@entities/booking";
import { fetchBookings, type BookingsListParams } from "@shared/api";
import { queryKeys, useNow } from "@shared/lib";

import {
  STUDIO_BOOKINGS_PAGE_SIZE,
  type StudioBookingsStatusFilter,
} from "./status-filter";

export function useStudioBookings(studioId: number) {
  const [statusFilter, setStatusFilter] =
    useState<StudioBookingsStatusFilter>("all");
  const now = useNow();

  const listParams = useMemo((): BookingsListParams => {
    const params: BookingsListParams = {
      studio_id: studioId,
      size: STUDIO_BOOKINGS_PAGE_SIZE,
    };
    if (statusFilter !== "all") {
      params.status = statusFilter;
    }
    return params;
  }, [statusFilter, studioId]);

  const query = useInfiniteQuery({
    queryKey: queryKeys.studio.bookings(studioId, listParams),
    queryFn: ({ pageParam }) =>
      fetchBookings({ ...listParams, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

  const bookings: BookingWithOccurrence[] = useMemo(
    () => (query.data?.pages ?? []).flatMap((page) => page.items),
    [query.data?.pages],
  );

  return {
    statusFilter,
    setStatusFilter,
    now,
    bookings,
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
