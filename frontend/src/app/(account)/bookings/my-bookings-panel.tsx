"use client";

import { useEffect, useMemo, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import {
  BookingCard,
  compareBookingsForBucket,
  getBookingListBucket,
  type BookingListBucket,
} from "@entities/booking";
import { fetchMyBookings, getUserFacingApiMessage } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { Button, Tabs } from "@shared/ui";
import {
  BookingsAllEmptyState,
  BookingsErrorState,
  BookingsSkeleton,
  BookingsTabEmptyState,
} from "./my-bookings-states";

const PAGE_SIZE = 20;

const LIST_PARAMS = {
  size: PAGE_SIZE,
  include_guest_email: true,
} as const;

const TABS: { id: BookingListBucket; label: string }[] = [
  { id: "upcoming", label: "Upcoming" },
  { id: "past", label: "Past" },
  { id: "cancelled", label: "Cancelled" },
];

export function MyBookingsPanel() {
  const [activeTab, setActiveTab] = useState<BookingListBucket>("upcoming");
  const [now] = useState(() => new Date());

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

  const tabBookings = useMemo(() => {
    return allBookings
      .filter((booking) => getBookingListBucket(booking, now) === activeTab)
      .sort((left, right) =>
        compareBookingsForBucket(activeTab, left, right),
      );
  }, [activeTab, allBookings, now]);

  // WHY: API has no tab filters — keep loading pages until the active tab
  // has rows or the envelope is exhausted (avoids false empty Cancelled).
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

  if (isLoading) {
    return <BookingsSkeleton />;
  }

  if (isError) {
    return (
      <BookingsErrorState
        message={getUserFacingApiMessage(error)}
        onRetry={() => refetch()}
      />
    );
  }

  if (totalCount === 0) {
    return <BookingsAllEmptyState />;
  }

  return (
    <div className="space-y-6" data-testid="my-bookings-panel">
      <Tabs
        tabs={TABS}
        activeTab={activeTab}
        onChange={(id) => setActiveTab(id as BookingListBucket)}
      />

      {tabBookings.length === 0 && !hasNextPage ? (
        <BookingsTabEmptyState bucket={activeTab} />
      ) : (
        <div className="space-y-3">
          {tabBookings.map((booking) => (
            <BookingCard
              key={booking.id}
              booking={booking}
              href={`/bookings/${booking.id}/confirm`}
              now={now}
            />
          ))}
        </div>
      )}

      {hasNextPage ? (
        <div className="flex justify-center">
          <Button
            type="button"
            variant="secondary"
            isLoading={isFetchingNextPage}
            onClick={() => void fetchNextPage()}
            data-testid="bookings-load-more"
          >
            Load more
          </Button>
        </div>
      ) : null}
    </div>
  );
}
