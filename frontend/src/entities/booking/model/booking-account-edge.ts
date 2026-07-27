import { BookingStatus, OccurrenceStatus } from "@shared/lib/constants";
import {
  isBookingReservationExpired,
  isCancelledBooking,
  isPendingBooking,
} from "./booking";

export type BookingAccountEdge =
  | {
      kind: "studio_cancelled";
      title: string;
      reason: string | null;
    }
  | {
      kind: "expired";
      title: string;
      description: string;
      rebookHref: string;
      rebookLabel: string;
    };

type EdgeBooking = {
  status: string;
  cancelled_at: string | null;
  reserved_until?: string | null;
  occurrence: {
    status: string;
    cancelled_at?: string | null;
    cancellation_reason?: string | null;
  };
  studio: { slug?: string | null };
};

/** True when the session itself was cancelled by the studio. */
export function isSessionCancelledByStudio(occurrence: {
  status: string;
}): boolean {
  return occurrence.status === OccurrenceStatus.CANCELLED;
}

export function getStudioRebookHref(studio: { slug?: string | null }): string {
  const slug = studio.slug?.trim();
  return slug ? `/s/${encodeURIComponent(slug)}` : "/studios";
}

/**
 * Account-list edge copy for STRATEGY §7:
 * - session cancelled by studio (+ reason)
 * - payment window / hold expired (+ rebook CTA target)
 */
export function getBookingAccountEdge(
  booking: EdgeBooking,
  now: Date = new Date(),
): BookingAccountEdge | null {
  if (isSessionCancelledByStudio(booking.occurrence)) {
    const reason = booking.occurrence.cancellation_reason?.trim() || null;
    return {
      kind: "studio_cancelled",
      title: "Session cancelled by the studio",
      reason,
    };
  }

  const isExpiredStatus = booking.status === BookingStatus.EXPIRED;
  const isHoldExpired =
    isPendingBooking(booking) && isBookingReservationExpired(booking, now);

  if (isExpiredStatus || isHoldExpired) {
    return {
      kind: "expired",
      title: "Payment window expired",
      description:
        "This hold timed out before payment. Book another slot to try again.",
      rebookHref: getStudioRebookHref(booking.studio),
      rebookLabel: "Book again",
    };
  }

  // Customer-cancelled without studio cancel — no special edge banner.
  if (isCancelledBooking(booking)) {
    return null;
  }

  return null;
}
