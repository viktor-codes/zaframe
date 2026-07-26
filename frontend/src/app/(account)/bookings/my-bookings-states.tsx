import Link from "next/link";
import type { BookingListBucket } from "@entities/booking";
import { Button, Skeleton } from "@shared/ui";

export function BookingsErrorState({
  message,
  onRetry,
}: {
  message: string;
  onRetry: () => void;
}) {
  return (
    <div
      className="rounded-2xl border border-red-200 bg-red-50 p-8 text-center text-red-800"
      data-testid="bookings-error"
    >
      <p className="font-medium">Could not load bookings</p>
      <p className="mt-1 text-sm">{message}</p>
      <Button type="button" className="mt-4" onClick={onRetry}>
        Try again
      </Button>
    </div>
  );
}

export function BookingsAllEmptyState() {
  return (
    <EmptyState
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
      <EmptyState
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
      <EmptyState
        title="No past sessions yet"
        description="After you attend a class, it will appear in this list."
        testId="bookings-empty-past"
      />
    );
  }

  return (
    <EmptyState
      title="No cancelled bookings"
      description="Cancellations — yours or the studio's — will show up here."
      testId="bookings-empty-cancelled"
    />
  );
}

export function BookingsSkeleton() {
  return (
    <div className="space-y-3" data-testid="bookings-loading">
      {Array.from({ length: 4 }).map((_, index) => (
        <div
          key={index}
          className="rounded-2xl border border-neutral-200 bg-white p-4"
        >
          <div className="space-y-2">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-56" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

interface EmptyStateProps {
  title: string;
  description: string;
  ctaHref?: string;
  ctaLabel?: string;
  testId: string;
}

function EmptyState({
  title,
  description,
  ctaHref,
  ctaLabel,
  testId,
}: EmptyStateProps) {
  return (
    <div
      className="rounded-2xl border border-neutral-200 bg-white p-10 text-center"
      data-testid={testId}
    >
      <p className="font-display text-lg font-semibold text-neutral-900">
        {title}
      </p>
      <p className="mt-2 text-sm text-neutral-600">{description}</p>
      {ctaHref && ctaLabel ? (
        <Button asChild className="mt-5">
          <Link href={ctaHref}>{ctaLabel}</Link>
        </Button>
      ) : null}
    </div>
  );
}
