import { BookingStatus } from "@shared/lib/constants";
import {
  canCustomerCancelBooking,
  isBookingReservationExpired,
  isCancelledBooking,
} from "./booking";

export type CancelPolicyHint =
  | { kind: "allowed"; deadlineLabel: string }
  | { kind: "closed"; cancelBeforeHours: number };

type CancelPolicyBooking = {
  status: string;
  cancelled_at: string | null;
  reserved_until?: string | null;
};

type CancelPolicyOccurrence = { start_time: string };
type CancelPolicyStudio = { cancel_before_hours: number };

/** Instant after which customer cancellation is blocked. */
export function getCancelDeadline(
  occurrenceStartIso: string,
  cancelBeforeHours: number,
): Date {
  return new Date(
    new Date(occurrenceStartIso).getTime() - cancelBeforeHours * 60 * 60 * 1000,
  );
}

function formatDeadline(deadline: Date): string {
  return deadline.toLocaleString("en-IE", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Customer-facing cancel policy copy for account / confirm UI.
 * Returns null when cancel is irrelevant (cancelled, expired hold, completed…).
 */
export function getCancelPolicyHint(
  booking: CancelPolicyBooking,
  occurrence: CancelPolicyOccurrence,
  studio: CancelPolicyStudio,
  now: Date = new Date(),
): CancelPolicyHint | null {
  if (isCancelledBooking(booking)) {
    return null;
  }

  if (isBookingReservationExpired(booking, now)) {
    return null;
  }

  if (
    booking.status !== BookingStatus.CONFIRMED &&
    booking.status !== BookingStatus.PENDING
  ) {
    return null;
  }

  if (canCustomerCancelBooking(booking, occurrence, studio, now)) {
    return {
      kind: "allowed",
      deadlineLabel: formatDeadline(
        getCancelDeadline(occurrence.start_time, studio.cancel_before_hours),
      ),
    };
  }

  return {
    kind: "closed",
    cancelBeforeHours: studio.cancel_before_hours,
  };
}
