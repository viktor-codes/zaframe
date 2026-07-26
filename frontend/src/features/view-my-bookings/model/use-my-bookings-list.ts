"use client";

import { useEffect, useMemo, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import {
  compareBookingsForBucket,
  getBookingListBucket,
  type BookingListBucket,
  type BookingSelfListItem,
} from "@entities/booking";
import { fetchMyBookings } from "@shared/api";
import { queryKeys, useNow } from "@shared/lib";

const LIST_PARAMS = { size: 20, include_guest_email: true } as const;

export interface UseMyBookingsListResult {
  activeTab: BookingListBucket;
  setActiveTab: (tab: BookingListBucket) => void;
  now: Date;
  tabBookings: BookingSelfListItem[];
  totalCount: number;
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refetch: () => void;
  fetchNextPage: () => void;
  hasNextPage: boolean;
  isFetchingNextPage: boolean;
}

/**
 * Paginated /bookings/my with client-side upcoming/past/cancelled tabs.
 * WHY: API has no bucket filters yet — auto-fetch fills an empty active tab.
 */
export function useMyBookingsList(): UseMyBookingsListResult {
  const [activeTab, setActiveTab] = useState<BookingListBucket>("upcoming");
  // WHY: hold countdown, cancel cutoff, and upcoming→past moves need a live clock.
  const now = useNow();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: queryKeys.bookings.my(LIST_PARAMS),
    queryFn: ({ pageParam }) =>
      fetchMyBookings({ ...LIST_PARAMS, page: pageParam }),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const loaded = lastPage.page * lastPage.size;
      return loaded < lastPage.total ? lastPage.page + 1 : undefined;
    },
  });

  const allBookings = useMemo(
    () => (data?.pages ?? []).flatMap((page) => page.items),
    [data?.pages],
  );

  const totalCount = data?.pages[0]?.total ?? 0;

  const tabBookings = useMemo(
    () =>
      allBookings
        .filter((booking) => getBookingListBucket(booking, now) === activeTab)
        .sort((a, b) => compareBookingsForBucket(activeTab, a, b)),
    [activeTab, allBookings, now],
  );

  useEffect(() => {
    if (isLoading || isFetchingNextPage || !hasNextPage) return;
    if (tabBookings.length === 0 && allBookings.length < totalCount) {
      void fetchNextPage();
    }
  }, [
    allBookings.length,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
    tabBookings.length,
    totalCount,
  ]);

  return {
    activeTab,
    setActiveTab,
    now,
    tabBookings,
    totalCount,
    isLoading,
    isError,
    error,
    refetch: () => {
      void refetch();
    },
    fetchNextPage: () => {
      void fetchNextPage();
    },
    hasNextPage: Boolean(hasNextPage),
    isFetchingNextPage,
  };
}
