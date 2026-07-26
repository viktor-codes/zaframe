import type { ScheduleTemplateResponse } from "./types";

/**
 * STRATEGY §4: template edits never mutate existing occurrences.
 * Prefer API `edit_behavior` when present; fall back to the locked product copy.
 */
export const DEFAULT_TEMPLATE_EDIT_WARNING =
  "Template changes affect future generations only. Edit existing sessions in the calendar.";

export function getScheduleTemplateEditWarning(
  template?: Pick<ScheduleTemplateResponse, "edit_behavior"> | null,
): string {
  const fromApi = template?.edit_behavior?.trim();
  return fromApi && fromApi.length > 0
    ? fromApi
    : DEFAULT_TEMPLATE_EDIT_WARNING;
}
