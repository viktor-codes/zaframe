import { BookingStatus } from "@shared/lib/constants";

export type BookingTimelineTone = "default" | "muted" | "danger" | "success";

export interface BookingTimelineEvent {
  id: string;
  label: string;
  at: string;
  tone: BookingTimelineTone;
  detail?: string;
}

type BookingTimelineInput = {
  status: string;
  created_at: string;
  reserved_until?: string | null;
  cancelled_at?: string | null;
  checked_in_at?: string | null;
  no_show_at?: string | null;
  occurrence: {
    start_time: string;
    end_time: string;
    status: string;
    cancelled_at?: string | null;
    cancellation_reason?: string | null;
  };
};

/**
 * Builds a chronological timeline of lifecycle events for account UI.
 * Only includes events backed by real timestamps from the API.
 */
export function getBookingTimelineEvents(
  booking: BookingTimelineInput,
): BookingTimelineEvent[] {
  const events: BookingTimelineEvent[] = [
    {
      id: "created",
      label: "Booked",
      at: booking.created_at,
      tone: "default",
    },
  ];

  if (booking.reserved_until) {
    events.push({
      id: "hold",
      label: "Hold until",
      at: booking.reserved_until,
      tone: "muted",
    });
  }

  events.push({
    id: "session",
    label: "Session",
    at: booking.occurrence.start_time,
    tone: "default",
  });

  if (
    booking.occurrence.status === "cancelled" &&
    booking.occurrence.cancelled_at
  ) {
    const reason = booking.occurrence.cancellation_reason?.trim();
    events.push({
      id: "occurrence-cancelled",
      label: "Session cancelled by the studio",
      at: booking.occurrence.cancelled_at,
      tone: "danger",
      detail: reason || undefined,
    });
  }

  if (booking.cancelled_at) {
    events.push({
      id: "booking-cancelled",
      label:
        booking.status === BookingStatus.CANCELLED
          ? "Booking cancelled"
          : "Cancelled",
      at: booking.cancelled_at,
      tone: "danger",
    });
  }

  if (booking.checked_in_at) {
    events.push({
      id: "checked-in",
      label: "Checked in",
      at: booking.checked_in_at,
      tone: "success",
    });
  }

  if (booking.no_show_at) {
    events.push({
      id: "no-show",
      label: "Marked no-show",
      at: booking.no_show_at,
      tone: "muted",
    });
  }

  return events.sort(
    (left, right) => new Date(left.at).getTime() - new Date(right.at).getTime(),
  );
}
