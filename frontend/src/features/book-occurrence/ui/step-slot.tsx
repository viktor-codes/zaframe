"use client";

import { OccurrenceRow, isOccurrenceBookable } from "@entities/occurrence";
import type { OccurrenceResponse } from "@entities/occurrence";
import { Skeleton } from "@shared/ui";

export interface StepSlotProps {
  occurrences: OccurrenceResponse[];
  isLoading: boolean;
  isError: boolean;
  selectedId: number | null;
  onSelect: (occurrence: OccurrenceResponse) => void;
  studioSlug: string;
}

export function StepSlot({
  occurrences,
  isLoading,
  isError,
  selectedId,
  onSelect,
  studioSlug,
}: StepSlotProps) {
  if (isLoading) {
    return (
      <div className="space-y-3" data-testid="book-step-slot-loading">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-24 w-full rounded-2xl" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-800">
        Could not load available times. Please try again.
      </div>
    );
  }

  const bookable = occurrences.filter((occurrence) =>
    isOccurrenceBookable(occurrence),
  );

  if (bookable.length === 0) {
    return (
      <div
        className="rounded-2xl border border-dashed border-neutral-200 bg-white px-6 py-10 text-center"
        data-testid="book-step-slot-empty"
      >
        <p className="font-display text-lg font-semibold text-neutral-900">
          No upcoming times
        </p>
        <p className="mt-2 text-sm text-neutral-600">
          Check back later, or pick another class from the studio page.
        </p>
        <a
          href={`/s/${encodeURIComponent(studioSlug)}`}
          className="mt-5 inline-flex text-sm font-semibold text-teal-700 underline"
        >
          Back to studio
        </a>
      </div>
    );
  }

  return (
    <ul className="space-y-3" data-testid="book-step-slot">
      {bookable.map((occurrence) => (
        <li key={occurrence.id}>
          <button
            type="button"
            className={`w-full rounded-2xl text-left transition ring-offset-2 focus-visible:ring-2 focus-visible:ring-teal-400 ${
              selectedId === occurrence.id
                ? "ring-2 ring-teal-500"
                : "hover:ring-1 hover:ring-neutral-300"
            }`}
            onClick={() => onSelect(occurrence)}
          >
            <OccurrenceRow
              occurrence={occurrence}
              className={
                selectedId === occurrence.id ? "border-teal-300" : undefined
              }
            />
          </button>
        </li>
      ))}
    </ul>
  );
}
