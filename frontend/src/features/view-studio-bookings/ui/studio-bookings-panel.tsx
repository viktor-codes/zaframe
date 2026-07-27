"use client";

import { StudioBookingCard } from "@entities/booking";
import { getUserFacingApiMessage } from "@shared/api";
import {
  Button,
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
  Tabs,
} from "@shared/ui";

import {
  STUDIO_BOOKINGS_STATUS_TABS,
  type StudioBookingsStatusFilter,
} from "../model/status-filter";
import { useStudioBookings } from "../model/use-studio-bookings";

export interface StudioBookingsPanelProps {
  studioId: number;
}

export function StudioBookingsPanel({ studioId }: StudioBookingsPanelProps) {
  const {
    statusFilter,
    setStatusFilter,
    now,
    bookings,
    totalCount,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useStudioBookings(studioId);

  if (isLoading) {
    return <ResourceListSkeleton testId="studio-bookings-skeleton" rows={4} />;
  }

  if (isError) {
    return (
      <ResourceErrorState
        title="Could not load bookings"
        message={getUserFacingApiMessage(error)}
        testId="studio-bookings-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="studio-bookings-panel">
      <div>
        <h1 className="text-secondary font-display text-2xl font-bold">
          Bookings
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Guests and payments for this studio. Filter by status to focus the
          day.
        </p>
      </div>

      <Tabs
        tabs={STUDIO_BOOKINGS_STATUS_TABS}
        activeTab={statusFilter}
        onChange={(id) => setStatusFilter(id as StudioBookingsStatusFilter)}
      />

      {totalCount === 0 ? (
        <ResourceEmptyState
          title={
            statusFilter === "all"
              ? "No bookings yet"
              : "No bookings in this view"
          }
          description={
            statusFilter === "all"
              ? "When customers book a session, they appear here with contact details."
              : "Try another status, or open Today to see today's sessions."
          }
          testId="studio-bookings-empty"
          ctaHref={`/dashboard/studios/${studioId}`}
          ctaLabel="Open Today"
        />
      ) : (
        <div className="space-y-3">
          {bookings.map((booking) => (
            <StudioBookingCard
              key={booking.id}
              booking={booking}
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
            onClick={() => {
              void fetchNextPage();
            }}
            data-testid="studio-bookings-load-more"
          >
            Load more
          </Button>
        </div>
      ) : null}
    </div>
  );
}
