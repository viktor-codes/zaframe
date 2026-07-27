import type { OccurrenceResponse } from "./types";

export interface OccurrenceDateGroup {
  /** Local calendar day `YYYY-MM-DD`. */
  dateKey: string;
  /** Human-readable day heading. */
  label: string;
  occurrences: OccurrenceResponse[];
}

function localDateKey(iso: string): string {
  const date = new Date(iso);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * Group occurrences by local calendar day, sorted ascending by start time.
 * STRATEGY §5: dashboard schedule is a list grouped by date (week view → P2).
 */
export function groupOccurrencesByDate(
  occurrences: readonly OccurrenceResponse[],
  locale = "en-IE",
): OccurrenceDateGroup[] {
  const sorted = [...occurrences].sort((a, b) =>
    a.start_time.localeCompare(b.start_time),
  );
  const byDay = new Map<string, OccurrenceResponse[]>();

  for (const occurrence of sorted) {
    const key = localDateKey(occurrence.start_time);
    const bucket = byDay.get(key);
    if (bucket) {
      bucket.push(occurrence);
    } else {
      byDay.set(key, [occurrence]);
    }
  }

  return [...byDay.entries()].map(([dateKey, dayOccurrences]) => ({
    dateKey,
    label: new Date(dayOccurrences[0].start_time).toLocaleDateString(locale, {
      weekday: "long",
      month: "long",
      day: "numeric",
      year: "numeric",
    }),
    occurrences: dayOccurrences,
  }));
}
