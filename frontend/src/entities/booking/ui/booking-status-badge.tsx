import {
  getBookingStatusPresentation,
  type BookingStatusTone,
} from "../model/booking-status";

export interface BookingStatusBadgeProps {
  status: string;
  paymentStatus?: string | null;
  reservedUntil?: string | null;
  /** When set, studio-cancelled sessions get a distinct badge label. */
  occurrenceStatus?: string | null;
  /** Injected clock for hold-expiry labels (tests / SSR-stable UI). */
  now?: Date;
  className?: string;
}

const toneClasses: Record<BookingStatusTone, string> = {
  neutral: "border-neutral-200 bg-neutral-100 text-neutral-700",
  amber: "border-amber-200 bg-amber-50 text-amber-900",
  green: "border-emerald-200 bg-emerald-50 text-emerald-900",
  red: "border-red-200 bg-red-50 text-red-800",
  teal: "border-teal-200 bg-teal-50 text-teal-800",
};

export function BookingStatusBadge({
  status,
  paymentStatus,
  reservedUntil,
  occurrenceStatus,
  now,
  className = "",
}: BookingStatusBadgeProps) {
  const { label, tone } = getBookingStatusPresentation(
    {
      status,
      payment_status: paymentStatus,
      reserved_until: reservedUntil,
      occurrenceStatus,
    },
    now,
  );

  return (
    <span
      className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-xs font-semibold ${toneClasses[tone]} ${className}`}
      data-testid="booking-status-badge"
      data-status={status}
    >
      {label}
    </span>
  );
}
