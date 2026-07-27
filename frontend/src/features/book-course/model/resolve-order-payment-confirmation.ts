/**
 * Map order status (post-Stripe redirect) to a success-page phase.
 *
 * WHY: Stripe Checkout success_url fires before the webhook may mark the order paid.
 */

import { OrderStatus } from "@shared/lib/constants";

export type OrderPaymentConfirmationPhase =
  | "processing"
  | "confirmed"
  | "manual_review"
  | "failed";

export type OrderPaymentConfirmationFailureReason =
  | "expired"
  | "cancelled"
  | "refunded"
  | "unknown";

export type OrderPaymentConfirmationResult =
  | { phase: "processing" }
  | { phase: "confirmed" }
  | { phase: "manual_review" }
  | { phase: "failed"; reason: OrderPaymentConfirmationFailureReason };

export interface OrderPaymentConfirmationInput {
  status: string;
}

export function resolveOrderPaymentConfirmation(
  order: OrderPaymentConfirmationInput,
): OrderPaymentConfirmationResult {
  if (order.status === OrderStatus.PAID) {
    return { phase: "confirmed" };
  }

  if (order.status === OrderStatus.MANUAL_REVIEW) {
    return { phase: "manual_review" };
  }

  if (order.status === OrderStatus.PENDING) {
    return { phase: "processing" };
  }

  if (order.status === OrderStatus.EXPIRED) {
    return { phase: "failed", reason: "expired" };
  }

  if (order.status === OrderStatus.CANCELLED) {
    return { phase: "failed", reason: "cancelled" };
  }

  if (order.status === OrderStatus.REFUNDED) {
    return { phase: "failed", reason: "refunded" };
  }

  return { phase: "failed", reason: "unknown" };
}

export function shouldContinueOrderPaymentConfirmationPoll(
  result: OrderPaymentConfirmationResult,
): boolean {
  return result.phase === "processing";
}
