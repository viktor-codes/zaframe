import type { ReactNode } from "react";
import {
  BookingTimeline,
  type BookingTimelineBooking,
} from "@entities/booking";
import { Card } from "@shared/ui";

type TimelineBookingSource = {
  status: string;
  created_at?: string;
  reserved_until?: string | null;
  cancelled_at?: string | null;
  checked_in_at?: string | null;
  no_show_at?: string | null;
};

type TimelineOccurrenceSource = {
  start_time: string;
  end_time: string;
  status: string;
  cancelled_at?: string | null;
  cancellation_reason?: string | null;
};

/**
 * Maps confirm-page booking + occurrence into entity timeline input.
 * Returns null for optimistic guest snapshots (no created_at yet).
 */
export function buildGuestConfirmTimelineBooking(
  booking: TimelineBookingSource,
  occurrence: TimelineOccurrenceSource,
): BookingTimelineBooking | null {
  if (!booking.created_at) {
    return null;
  }

  return {
    status: booking.status,
    created_at: booking.created_at,
    reserved_until: booking.reserved_until ?? null,
    cancelled_at: booking.cancelled_at ?? null,
    checked_in_at: booking.checked_in_at ?? null,
    no_show_at: booking.no_show_at ?? null,
    occurrence: {
      start_time: occurrence.start_time,
      end_time: occurrence.end_time,
      status: occurrence.status,
      cancelled_at: occurrence.cancelled_at ?? null,
      cancellation_reason: occurrence.cancellation_reason ?? null,
    },
  };
}

/** Timeline card for confirm active/inactive views, or null while snapshot-only. */
export function guestConfirmTimelineSlot(
  booking: TimelineBookingSource,
  occurrence: TimelineOccurrenceSource | undefined,
): ReactNode {
  if (occurrence == null) return null;
  const timelineBooking = buildGuestConfirmTimelineBooking(booking, occurrence);
  if (timelineBooking == null) return null;
  return <GuestBookingConfirmTimeline booking={timelineBooking} />;
}

export function GuestBookingConfirmTimeline({
  booking,
  className = "",
}: {
  booking: BookingTimelineBooking;
  className?: string;
}) {
  return (
    <Card
      className={`mb-6 p-5 ${className}`}
      data-testid="guest-confirm-timeline"
    >
      <h2 className="mb-4 text-sm font-semibold tracking-wide text-neutral-900 uppercase">
        Timeline
      </h2>
      <BookingTimeline booking={booking} />
    </Card>
  );
}
