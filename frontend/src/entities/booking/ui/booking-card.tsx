import Link from "next/link";
import type { ReactNode } from "react";
import { formatMoneyFromCents } from "@shared/lib";
import type { BookingSelfListItem } from "../model/types";
import { BookingStatusBadge } from "./booking-status-badge";

export interface BookingCardProps {
  booking: BookingSelfListItem;
  href?: string;
  className?: string;
  /** Feature-level actions (cancel, pay) — never business logic here. */
  actions?: ReactNode;
  /** Injected clock for hold-expiry badge labels. */
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

export function BookingCard({
  booking,
  href,
  className = "",
  actions,
  now,
}: BookingCardProps) {
  const { occurrence, studio } = booking;
  const priceLabel =
    occurrence.price_cents === 0
      ? "Free"
      : formatMoneyFromCents(occurrence.price_cents);

  const body = (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between sm:gap-4">
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="truncate font-display text-base font-semibold text-neutral-900">
            {studio.name}
          </h3>
          <BookingStatusBadge
            status={booking.status}
            paymentStatus={booking.payment_status}
            reservedUntil={booking.reserved_until}
            now={now}
          />
        </div>
        <p className="truncate text-sm text-neutral-600">{occurrence.title}</p>
        <p className="text-sm text-neutral-500">
          {formatSessionWhen(occurrence.start_time, occurrence.end_time)}
        </p>
      </div>

      <div className="flex shrink-0 items-center justify-between gap-3 sm:flex-col sm:items-end sm:justify-center">
        <p className="font-mono text-base font-bold text-teal-600">
          {priceLabel}
        </p>
        {href ? (
          <span className="text-sm font-medium text-neutral-900">
            View details →
          </span>
        ) : null}
      </div>
    </div>
  );

  return (
    <article
      className={`rounded-2xl border border-neutral-200 bg-white p-4 ${className}`}
      data-testid="booking-card"
      data-booking-id={booking.id}
    >
      {href ? (
        <Link
          href={href}
          className="block rounded-xl outline-offset-4 transition-opacity hover:opacity-90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-neutral-900"
        >
          {body}
        </Link>
      ) : (
        body
      )}
      {actions ? (
        <div className="mt-3 border-t border-neutral-100 pt-3">{actions}</div>
      ) : null}
    </article>
  );
}
