import { z } from "zod";

import type {
  ScheduleTemplateCreate,
  ScheduleTemplateUpdate,
} from "@entities/schedule-template";

import {
  emptyTemplateForm,
  type TemplateFormValues,
} from "./schedule-form-values";
import { normalizeStartTime, TIME_RE, DATE_RE } from "./schedule-form-shared";

type TemplateErrorMap = Partial<Record<keyof TemplateFormValues, string>>;

const TemplateFormSchema = z
  .object({
    day_of_week: z.coerce
      .number({ error: "Pick a day of the week" })
      .int()
      .min(0, "Pick a day of the week")
      .max(6, "Pick a day of the week"),
    start_time: z
      .string()
      .trim()
      .regex(TIME_RE, "Enter a valid time (e.g. 18:00)"),
    valid_from: z.string().trim().regex(DATE_RE, "Enter a valid start date"),
    valid_to: z
      .string()
      .trim()
      .transform((value) => (value.length > 0 ? value : null))
      .refine((value) => value === null || DATE_RE.test(value), {
        message: "Enter a valid end date",
      }),
  })
  .superRefine((value, ctx) => {
    if (value.valid_to != null && value.valid_to < value.valid_from) {
      ctx.addIssue({
        code: "custom",
        path: ["valid_to"],
        message: "End date must be on or after the start date",
      });
    }
  });

function collectTemplateErrors(error: z.ZodError): TemplateErrorMap {
  const errors: TemplateErrorMap = {};
  const keys = Object.keys(emptyTemplateForm()) as (keyof TemplateFormValues)[];
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (
      typeof key === "string" &&
      keys.includes(key as keyof TemplateFormValues) &&
      !errors[key as keyof TemplateFormValues]
    ) {
      errors[key as keyof TemplateFormValues] = issue.message;
    }
  }
  return errors;
}

export function parseCreateTemplate(input: TemplateFormValues): {
  data: ScheduleTemplateCreate | null;
  errors: TemplateErrorMap;
} {
  const result = TemplateFormSchema.safeParse(input);
  if (!result.success) {
    return { data: null, errors: collectTemplateErrors(result.error) };
  }
  return {
    data: {
      day_of_week: result.data.day_of_week,
      start_time: normalizeStartTime(result.data.start_time),
      valid_from: result.data.valid_from,
      valid_to: result.data.valid_to,
    },
    errors: {},
  };
}

export function parseUpdateTemplate(input: TemplateFormValues): {
  data: ScheduleTemplateUpdate | null;
  errors: TemplateErrorMap;
} {
  const parsed = parseCreateTemplate(input);
  if (!parsed.data) {
    return { data: null, errors: parsed.errors };
  }
  return {
    data: {
      day_of_week: parsed.data.day_of_week,
      start_time: parsed.data.start_time,
      valid_from: parsed.data.valid_from,
      valid_to: parsed.data.valid_to,
    },
    errors: {},
  };
}
