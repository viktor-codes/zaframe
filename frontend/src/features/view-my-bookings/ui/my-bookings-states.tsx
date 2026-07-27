import type { BookingListBucket } from "@entities/booking";
import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

export function BookingsErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <ResourceErrorState
      title="Could not load bookings"
      message={message}
      testId="bookings-error"
      onRetry={onRetry}
    />
  );
}

export function BookingsAllEmptyState() {
  return (
    <ResourceEmptyState
      title="No bookings yet"
      description="Reserve a studio session — it will show up here with payment and cancel options."
      ctaHref="/studios"
      ctaLabel="Browse studios"
      testId="bookings-empty-all"
    />
  );
}

export function BookingsTabEmptyState({
  bucket,
}: {
  bucket: BookingListBucket;
}) {
  if (bucket === "upcoming") {
    return (
      <ResourceEmptyState
        title="Nothing coming up"
        description="Browse studios and book a seat — your next session will land here."
        ctaHref="/studios"
        ctaLabel="Find a session"
        testId="bookings-empty-upcoming"
      />
    );
  }

  if (bucket === "past") {
    return (
      <ResourceEmptyState
        title="No past sessions yet"
        description="After you attend a class, it will appear in this list."
        testId="bookings-empty-past"
      />
    );
  }

  return (
    <ResourceEmptyState
      title="No cancelled bookings"
      description="Cancellations — yours or the studio's — and expired holds will show up here."
      testId="bookings-empty-cancelled"
    />
  );
}

export function BookingsSkeleton() {
  return <ResourceListSkeleton testId="bookings-loading" rows={4} />;
}
