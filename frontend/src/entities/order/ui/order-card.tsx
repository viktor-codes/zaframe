import {
  formatOrderTotal,
  getOrderBookingCount,
} from "../model/order";
import { getOrderStatusPresentation } from "../model/order-status";
import type { OrderListItem } from "../model/types";
import { OrderStatusBadge } from "./order-status-badge";

export interface OrderCardProps {
  order: OrderListItem;
  className?: string;
}

function formatOrderedAt(iso: string): string {
  return new Date(iso).toLocaleString("en-IE", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function OrderCard({ order, className = "" }: OrderCardProps) {
  const sessionCount = getOrderBookingCount(order);
  const sessionsLabel =
    sessionCount === 1 ? "1 session" : `${sessionCount} sessions`;
  const title = order.service?.name?.trim() || `Course order #${order.id}`;
  const { detail } = getOrderStatusPresentation(order.status);

  return (
    <article
      className={`rounded-2xl border border-neutral-200 bg-white p-4 ${className}`}
      data-testid="order-card"
      data-order-id={order.id}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-display text-base font-semibold text-neutral-900">
              {title}
            </h3>
            <OrderStatusBadge status={order.status} />
          </div>
          <p className="text-sm text-neutral-600">
            {sessionsLabel} · Ordered {formatOrderedAt(order.created_at)}
          </p>
          {detail ? (
            <p className="text-sm text-amber-800" data-testid="order-status-detail">
              {detail}
            </p>
          ) : null}
        </div>

        <p className="shrink-0 font-mono text-base font-bold text-teal-600">
          {formatOrderTotal(order)}
        </p>
      </div>
    </article>
  );
}
