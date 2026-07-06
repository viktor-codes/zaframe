import type { OrderLike, OrderListItem } from "./types";

export const ORDER_STATUS = {
  PENDING: "pending",
  PAID: "paid",
  REFUNDED: "refunded",
  CANCELLED: "cancelled",
  EXPIRED: "expired",
  MANUAL_REVIEW: "manual_review",
} as const;

type OrderState = Pick<OrderLike, "status" | "total_amount_cents" | "currency">;

export function isPendingOrder(order: Pick<OrderState, "status">): boolean {
  return order.status === ORDER_STATUS.PENDING;
}

export function isPaidOrder(order: Pick<OrderState, "status">): boolean {
  return order.status === ORDER_STATUS.PAID;
}

export function isManualReviewOrder(order: Pick<OrderState, "status">): boolean {
  return order.status === ORDER_STATUS.MANUAL_REVIEW;
}

export function getOrderBookingCount(
  order: Pick<OrderListItem, "bookings">,
): number {
  return order.bookings?.length ?? 0;
}

export function formatOrderTotal(
  order: Pick<OrderState, "total_amount_cents" | "currency">,
  locale = "en-IE",
): string {
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: order.currency.toUpperCase(),
  }).format(order.total_amount_cents / 100);
}
