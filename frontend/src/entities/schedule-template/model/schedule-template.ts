import { getDayOfWeekLabel } from "./day-of-week";
import type { ScheduleTemplateResponse } from "./types";

/**
 * Normalise API wall-clock time (`HH:MM` or `HH:MM:SS`) for UI display.
 */
export function formatTemplateStartTime(startTime: string): string {
  const trimmed = startTime.trim();
  const match = /^(\d{1,2}):(\d{2})(?::\d{2})?$/.exec(trimmed);
  if (!match) {
    return trimmed;
  }
  const hours = match[1].padStart(2, "0");
  const minutes = match[2];
  return `${hours}:${minutes}`;
}

export function formatScheduleTemplateSummary(
  template: Pick<ScheduleTemplateResponse, "day_of_week" | "start_time">,
): string {
  return `${getDayOfWeekLabel(template.day_of_week)} at ${formatTemplateStartTime(template.start_time)}`;
}
