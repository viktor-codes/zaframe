import type { StudioOccurrencesParams } from "@shared/api";

/** Default window: local today → +8 weeks (matches generate default horizon). */
export const CALENDAR_DEFAULT_WEEKS = 8;
/** Page size for calendar infinite list (envelope `total` drives Load more). */
export const CALENDAR_PAGE_SIZE = 20;

export type CalendarStatusFilter = "all" | "scheduled" | "cancelled" | "completed";

export function buildCalendarParams(
  statusFilter: CalendarStatusFilter,
  now: Date = new Date(),
): StudioOccurrencesParams {
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);
  const end = new Date(start);
  end.setDate(end.getDate() + CALENDAR_DEFAULT_WEEKS * 7);

  const params: StudioOccurrencesParams = {
    start_from: start.toISOString(),
    start_to: end.toISOString(),
    size: CALENDAR_PAGE_SIZE,
  };

  if (statusFilter !== "all") {
    params.status = statusFilter;
  }

  return params;
}
