import {
  getOrderStatusPresentation,
  type OrderStatusTone,
} from "../model/order-status";

export interface OrderStatusBadgeProps {
  status: string;
  className?: string;
}

const toneClasses: Record<OrderStatusTone, string> = {
  neutral: "border-neutral-200 bg-neutral-100 text-neutral-700",
  amber: "border-amber-200 bg-amber-50 text-amber-900",
  green: "border-emerald-200 bg-emerald-50 text-emerald-900",
  red: "border-red-200 bg-red-50 text-red-800",
  teal: "border-teal-200 bg-teal-50 text-teal-800",
};

export function OrderStatusBadge({
  status,
  className = "",
}: OrderStatusBadgeProps) {
  const { label, tone } = getOrderStatusPresentation(status);

  return (
    <span
      className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]} ${className}`}
      data-testid="order-status-badge"
      data-status={status}
    >
      {label}
    </span>
  );
}
