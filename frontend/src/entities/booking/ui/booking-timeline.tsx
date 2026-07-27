import {
  getBookingTimelineEvents,
  type BookingTimelineTone,
} from "../model/booking-timeline";

/** Minimal booking shape for timeline — list items or detail + occurrence. */
export type BookingTimelineBooking = {
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

export interface BookingTimelineProps {
  booking: BookingTimelineBooking;
  className?: string;
}

const toneDotClasses: Record<BookingTimelineTone, string> = {
  default: "bg-neutral-900",
  muted: "bg-neutral-400",
  danger: "bg-red-500",
  success: "bg-emerald-500",
};

function formatTimelineWhen(iso: string): string {
  return new Date(iso).toLocaleString("en-IE", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function BookingTimeline({
  booking,
  className = "",
}: BookingTimelineProps) {
  const events = getBookingTimelineEvents(booking);

  return (
    <ol
      className={`space-y-0 ${className}`}
      data-testid="booking-timeline"
      aria-label="Booking timeline"
    >
      {events.map((event, index) => {
        const isLast = index === events.length - 1;

        return (
          <li key={event.id} className="relative flex gap-3 pb-5 last:pb-0">
            {!isLast ? (
              <span
                className="absolute top-3 left-[5px] h-[calc(100%-4px)] w-px bg-neutral-200"
                aria-hidden
              />
            ) : null}
            <span
              className={`relative z-10 mt-1.5 size-2.5 shrink-0 rounded-full ${toneDotClasses[event.tone]}`}
              aria-hidden
            />
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-neutral-900">
                {event.label}
              </p>
              <p className="text-xs text-neutral-500">
                {formatTimelineWhen(event.at)}
              </p>
              {event.detail ? (
                <p className="mt-1 text-sm text-neutral-600">{event.detail}</p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
