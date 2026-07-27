import { formatMoneyFromCents } from "@shared/lib";

import type { BookingWithOccurrence } from "../model/types";
import { BookingStatusBadge } from "./booking-status-badge";

export interface StudioBookingCardProps {
  booking: BookingWithOccurrence;
  className?: string;
  now?: Date;
}

function formatSessionWhen(startIso: string, endIso: string): string {
  const start = new Date(startIso);
  const end = new Date(endIso);
  const date = start.toLocaleDateString("en-IE", {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
  const time = `${start.toLocaleTimeString("en-IE", {
    hour: "2-digit",
    minute: "2-digit",
  })} – ${end.toLocaleTimeString("en-IE", {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
  return `${date} · ${time}`;
}

function guestLabel(booking: BookingWithOccurrence): string {
  const name = booking.guest_name?.trim();
  if (name) return name;
  const email = booking.guest_email?.trim();
  if (email) return email;
  return `Booking #${booking.id}`;
}

/**
 * Studio-staff booking row: guest first, then session context.
 * WHY: customer BookingCard leads with studio name — wrong for dashboard.
 */
export function StudioBookingCard({
  booking,
  className = "",
  now,
}: StudioBookingCardProps) {
  const { occurrence } = booking;
  const priceLabel =
    occurrence.price_cents === 0
      ? "Free"
      : formatMoneyFromCents(occurrence.price_cents);
  const contactParts = [booking.guest_email, booking.guest_phone].filter(
    (value): value is string => Boolean(value?.trim()),
  );

  return (
    <article
      className={`rounded-2xl border border-neutral-200 bg-white p-4 ${className}`}
      data-testid="studio-booking-card"
      data-booking-id={booking.id}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="truncate font-display text-base font-semibold text-neutral-900">
              {guestLabel(booking)}
            </h3>
            <BookingStatusBadge
              status={booking.status}
              paymentStatus={booking.payment_status}
              reservedUntil={booking.reserved_until}
              occurrenceStatus={occurrence.status}
              now={now}
            />
          </div>
          <p className="truncate text-sm text-neutral-600">
            {occurrence.title}
          </p>
          <p className="text-sm text-neutral-500">
            {formatSessionWhen(occurrence.start_time, occurrence.end_time)}
          </p>
          {contactParts.length > 0 ? (
            <p className="truncate text-xs text-neutral-500">
              {contactParts.join(" · ")}
            </p>
          ) : null}
        </div>

        <p className="shrink-0 font-mono text-base font-bold text-teal-600">
          {priceLabel}
        </p>
      </div>
    </article>
  );
}
