import Link from "next/link";
import { getOccurrenceBookActionLabel } from "../model/occurrence-action-label";
import {
  getOccurrenceDurationMinutes,
  getOccurrenceInstructorName,
  isOccurrenceBookable,
  isOccurrenceFull,
  type OccurrenceCapacityCounts,
} from "../model/occurrence";
import type { OccurrenceResponse } from "../model/types";
import { CapacityIndicator } from "./capacity-indicator";

export interface OccurrenceRowProps {
  occurrence: OccurrenceResponse;
  /** When omitted, capacity UI is hidden (list APIs may not include counts yet). */
  capacity?: Pick<
    OccurrenceCapacityCounts,
    "confirmed_count" | "pending_count"
  >;
  href?: string;
  className?: string;
  /** Optional label override for the CTA. */
  actionLabel?: string;
}

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-EU", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function formatSlot(startIso: string, endIso: string): {
  date: string;
  time: string;
} {
  const start = new Date(startIso);
  const end = new Date(endIso);

  return {
    date: start.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    }),
    time: `${start.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    })} – ${end.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    })}`,
  };
}

export function OccurrenceRow({
  occurrence,
  capacity,
  href,
  className = "",
  actionLabel = "Book",
}: OccurrenceRowProps) {
  const { date, time } = formatSlot(occurrence.start_time, occurrence.end_time);
  const instructor = getOccurrenceInstructorName(occurrence);
  const durationMinutes = getOccurrenceDurationMinutes(occurrence);
  const capacityCounts =
    capacity != null
      ? {
          max_capacity: occurrence.max_capacity,
          confirmed_count: capacity.confirmed_count,
          pending_count: capacity.pending_count ?? 0,
        }
      : null;
  const isFull = capacityCounts != null && isOccurrenceFull(capacityCounts);
  const canBook = isOccurrenceBookable(occurrence) && !isFull;
  const showAction = Boolean(href);

  return (
    <article
      className={`flex flex-col gap-3 rounded-2xl border border-neutral-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between sm:gap-4 ${className}`}
      data-testid="occurrence-row"
    >
      <div className="min-w-0 flex-1 space-y-1">
        <div className="flex flex-wrap items-center gap-2">
          <h3 className="truncate font-display text-base font-semibold text-neutral-900">
            {occurrence.title}
          </h3>
          {capacityCounts ? <CapacityIndicator {...capacityCounts} /> : null}
        </div>
        <p className="text-sm text-neutral-600">
          {date} · {time}
          <span className="text-neutral-400"> · {durationMinutes} min</span>
        </p>
        {instructor ? (
          <p className="text-xs text-neutral-500">with {instructor}</p>
        ) : null}
      </div>

      <div className="flex shrink-0 items-center justify-between gap-3 sm:flex-col sm:items-end sm:justify-center">
        <p className="font-mono text-base font-bold text-teal-600">
          {formatPrice(occurrence.price_cents)}
        </p>
        {showAction ? (
          canBook ? (
            <Link
              href={href!}
              className="inline-flex items-center justify-center rounded-xl bg-neutral-900 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-neutral-800"
              data-testid="occurrence-row-book"
            >
              {actionLabel}
            </Link>
          ) : (
            <span
              className="inline-flex items-center justify-center rounded-xl bg-neutral-100 px-4 py-2 text-sm font-semibold text-neutral-400"
              data-testid="occurrence-row-book-disabled"
              aria-disabled
            >
              {getOccurrenceBookActionLabel({ isFull, canBook })}
            </span>
          )
        ) : null}
      </div>
    </article>
  );
}
