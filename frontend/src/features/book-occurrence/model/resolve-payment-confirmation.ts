/**
 * Map booking + payment_status (post-Stripe redirect) to a success-page phase.
 *
 * WHY: Stripe Checkout success_url fires before the webhook may confirm the booking.
 * The UI must poll and not assume confirmation from the redirect alone.
 */

import {
  BookingPaymentStatus,
  BookingStatus,
} from "@shared/lib/constants";

export type PaymentConfirmationPhase =
  | "processing"
  | "confirmed"
  | "manual_review"
  | "failed";

export type PaymentConfirmationFailureReason =
  | "expired"
  | "cancelled"
  | "failed_payment"
  | "unknown";

export type PaymentConfirmationResult =
  | { phase: "processing" }
  | { phase: "confirmed" }
  | { phase: "manual_review" }
  | { phase: "failed"; reason: PaymentConfirmationFailureReason };

export interface PaymentConfirmationInput {
  status: string;
  payment_status?: string | null;
}

const MANUAL_REVIEW_PAYMENT_STATUSES: readonly string[] = [
  BookingPaymentStatus.MANUAL_REVIEW,
  BookingPaymentStatus.OVERBOOKED_MANUAL_REVIEW,
];

const FAILED_PAYMENT_STATUSES: readonly string[] = [
  BookingPaymentStatus.FAILED,
];

export function resolvePaymentConfirmation(
  booking: PaymentConfirmationInput,
): PaymentConfirmationResult {
  const paymentStatus = booking.payment_status ?? null;

  if (
    paymentStatus != null &&
    MANUAL_REVIEW_PAYMENT_STATUSES.includes(paymentStatus)
  ) {
    return { phase: "manual_review" };
  }

  if (booking.status === BookingStatus.CONFIRMED) {
    return { phase: "confirmed" };
  }

  if (
    paymentStatus === BookingPaymentStatus.SUCCEEDED &&
    booking.status === BookingStatus.PENDING
  ) {
    // WHY: rare race — ledger updated before booking.status flip; keep polling.
    return { phase: "processing" };
  }

  if (booking.status === BookingStatus.EXPIRED) {
    return { phase: "failed", reason: "expired" };
  }

  if (booking.status === BookingStatus.CANCELLED) {
    return { phase: "failed", reason: "cancelled" };
  }

  if (
    paymentStatus != null &&
    FAILED_PAYMENT_STATUSES.includes(paymentStatus)
  ) {
    return { phase: "failed", reason: "failed_payment" };
  }

  if (booking.status === BookingStatus.PENDING) {
    return { phase: "processing" };
  }

  return { phase: "failed", reason: "unknown" };
}

/** Keep refetching while the webhook may still arrive. */
export function shouldContinuePaymentConfirmationPoll(
  result: PaymentConfirmationResult,
): boolean {
  return result.phase === "processing";
}
