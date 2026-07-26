import type { StudioOccurrencesParams } from "@shared/api";

/** Enough for a busy studio day without a second page in MVP. */
export const TODAY_PAGE_SIZE = 100;

/**
 * API params for the studio "Today" window: local midnight → next midnight.
 *
 * WHY: matches `buildCalendarParams` local-day semantics so Calendar and Today
 * agree on which sessions belong to "today". Studio-timezone day bounds → later.
 */
export function buildTodayParams(now: Date = new Date()): StudioOccurrencesParams {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);

  return {
    start_from: start.toISOString(),
    start_to: end.toISOString(),
    status: "scheduled",
    size: TODAY_PAGE_SIZE,
  };
}

/** Day heading for the Today screen (e.g. "Sunday, 26 July"). */
export function formatTodayHeading(
  now: Date = new Date(),
  locale = "en-IE",
): string {
  return now.toLocaleDateString(locale, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}
