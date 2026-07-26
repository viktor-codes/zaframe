import { z } from "zod";

import type { ScheduleGenerateRequest } from "@entities/schedule-template";

import {
  emptyGenerateForm,
  type GenerateFormValues,
} from "./schedule-form-values";
import { normalizeStartTime, TIME_RE } from "./schedule-form-shared";

type GenerateErrorMap = Partial<
  Record<keyof GenerateFormValues | "days", string>
>;

const GenerateFormSchema = z.object({
  days: z
    .array(
      z.coerce
        .number()
        .int()
        .min(0, "Each day must be Monday–Sunday")
        .max(6, "Each day must be Monday–Sunday"),
    )
    .min(1, "Pick at least one day")
    .refine((days) => new Set(days).size === days.length, {
      message: "Days must not contain duplicates",
    }),
  start_time: z
    .string()
    .trim()
    .regex(TIME_RE, "Enter a valid time (e.g. 18:00)"),
  weeks_count: z.coerce
    .number({ error: "Enter weeks to generate" })
    .int("Weeks must be a whole number")
    .min(1, "Generate at least 1 week")
    .max(52, "Generate at most 52 weeks"),
});

function collectGenerateErrors(error: z.ZodError): GenerateErrorMap {
  const errors: GenerateErrorMap = {};
  const keys = Object.keys(emptyGenerateForm()) as (keyof GenerateFormValues)[];
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (
      typeof key === "string" &&
      (keys.includes(key as keyof GenerateFormValues) || key === "days") &&
      !errors[key as keyof GenerateErrorMap]
    ) {
      errors[key as keyof GenerateErrorMap] = issue.message;
    }
  }
  return errors;
}

export function parseGenerateOccurrences(
  input: GenerateFormValues,
  serviceId: number,
): { data: ScheduleGenerateRequest | null; errors: GenerateErrorMap } {
  const result = GenerateFormSchema.safeParse({
    days: input.days,
    start_time: input.start_time,
    weeks_count: input.weeks_count,
  });
  if (!result.success) {
    return { data: null, errors: collectGenerateErrors(result.error) };
  }
  return {
    data: {
      service_id: serviceId,
      days: result.data.days,
      start_time: normalizeStartTime(result.data.start_time),
      weeks_count: result.data.weeks_count,
    },
    errors: {},
  };
}
