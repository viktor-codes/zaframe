import {
  formatTemplateStartTime,
  type ScheduleTemplateResponse,
} from "@entities/schedule-template";

export interface TemplateFormValues {
  day_of_week: string;
  start_time: string;
  valid_from: string;
  valid_to: string;
}

export interface GenerateFormValues {
  /** Day-of-week values as strings for checkbox state. */
  days: string[];
  start_time: string;
  weeks_count: string;
}

export function todayLocalIsoDate(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function emptyTemplateForm(
  overrides: Partial<TemplateFormValues> = {},
): TemplateFormValues {
  return {
    day_of_week: "1",
    start_time: "18:00",
    valid_from: todayLocalIsoDate(),
    valid_to: "",
    ...overrides,
  };
}

export function templateToFormValues(
  template: ScheduleTemplateResponse,
): TemplateFormValues {
  return emptyTemplateForm({
    day_of_week: String(template.day_of_week),
    start_time: formatTemplateStartTime(template.start_time),
    valid_from: template.valid_from,
    valid_to: template.valid_to ?? "",
  });
}

export function emptyGenerateForm(
  overrides: Partial<GenerateFormValues> = {},
): GenerateFormValues {
  return {
    days: ["1"],
    start_time: "18:00",
    weeks_count: "6",
    ...overrides,
  };
}

/** Prefill generate form from saved templates (days union + first start time). */
export function suggestGenerateFromTemplates(
  templates: readonly ScheduleTemplateResponse[],
): GenerateFormValues {
  if (templates.length === 0) {
    return emptyGenerateForm();
  }
  const days = [
    ...new Set(templates.map((template) => String(template.day_of_week))),
  ].sort((a, b) => Number(a) - Number(b));
  return emptyGenerateForm({
    days,
    start_time: formatTemplateStartTime(templates[0].start_time),
  });
}
