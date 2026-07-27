"use client";

import type { ReactNode } from "react";
import {
  BookingCard,
  type BookingListBucket,
  type BookingSelfListItem,
} from "@entities/booking";
import { getUserFacingApiMessage } from "@shared/api";
import { Button, Tabs } from "@shared/ui";
import { useMyBookingsList } from "../model/use-my-bookings-list";
import {
  BookingsAllEmptyState,
  BookingsErrorState,
  BookingsSkeleton,
  BookingsTabEmptyState,
} from "./my-bookings-states";

const TABS: { id: BookingListBucket; label: string }[] = [
  { id: "upcoming", label: "Upcoming" },
  { id: "past", label: "Past" },
  { id: "cancelled", label: "Cancelled" },
];

export interface MyBookingsActionContext {
  booking: BookingSelfListItem;
  now: Date;
  bucket: BookingListBucket;
}

export interface MyBookingsPanelProps {
  /**
   * App-layer actions (pay / cancel).
   * WHY: features must not import other features (e.g. cancel-booking).
   */
  renderActions?: (ctx: MyBookingsActionContext) => ReactNode;
}

export function MyBookingsPanel({ renderActions }: MyBookingsPanelProps) {
  const {
    activeTab,
    setActiveTab,
    now,
    tabBookings,
    totalCount,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useMyBookingsList();

  if (isLoading) {
    return <BookingsSkeleton />;
  }

  if (isError) {
    return (
      <BookingsErrorState
        message={getUserFacingApiMessage(error)}
        onRetry={refetch}
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
              actions={
                renderActions?.({
                  booking,
                  now,
                  bucket: activeTab,
                }) ?? null
              }
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
            onClick={fetchNextPage}
            data-testid="bookings-load-more"
          >
            Load more
          </Button>
        </div>
      ) : null}
    </div>
  );
}
