import { OrderStatus } from "@shared/lib/constants";

export type OrderStatusTone = "neutral" | "amber" | "green" | "red" | "teal";

export interface OrderStatusPresentation {
  label: string;
  tone: OrderStatusTone;
  /** Optional secondary line for edge statuses (manual_review, expired). */
  detail?: string;
}

/**
 * Customer-facing label + tone for an order status badge.
 */
export function getOrderStatusPresentation(
  status: string,
): OrderStatusPresentation {
  if (status === OrderStatus.PAID) {
    return { label: "Paid", tone: "green" };
  }

  if (status === OrderStatus.PENDING) {
    return { label: "Pending payment", tone: "amber" };
  }

  if (status === OrderStatus.EXPIRED) {
    return {
      label: "Expired",
      tone: "red",
      detail: "Payment window expired — book the course again to continue.",
    };
  }

  if (status === OrderStatus.CANCELLED) {
    return { label: "Cancelled", tone: "neutral" };
  }

  if (status === OrderStatus.REFUNDED) {
    return { label: "Refunded", tone: "neutral" };
  }

  if (status === OrderStatus.MANUAL_REVIEW) {
    return {
      label: "Under review",
      tone: "amber",
      detail: "Payment is being verified. Contact support if this persists.",
    };
  }

  return { label: formatUnknownStatus(status), tone: "neutral" };
}

function formatUnknownStatus(status: string): string {
  if (!status) return "Unknown";
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
