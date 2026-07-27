import { z } from "zod";

import type { OccurrenceUpdate } from "@entities/occurrence";
import { OccurrenceStatus } from "@shared/lib";

import { fromDatetimeLocalValue } from "./datetime-local";

export interface OccurrenceEditFormValues {
  title: string;
  start_time: string;
  end_time: string;
  max_capacity: string;
}

export interface OccurrenceCancelFormValues {
  cancellation_reason: string;
}

type EditErrorMap = Partial<Record<keyof OccurrenceEditFormValues, string>>;
type CancelErrorMap = Partial<Record<keyof OccurrenceCancelFormValues, string>>;

const EditSchema = z
  .object({
    title: z.string().trim().min(1, "Enter a title").max(200),
    start_time: z.string().trim().min(1, "Enter a start time"),
    end_time: z.string().trim().min(1, "Enter an end time"),
    max_capacity: z.coerce
      .number({ error: "Capacity must be at least 1" })
      .int()
      .min(1, "Capacity must be at least 1"),
  })
  .superRefine((value, ctx) => {
    const start = new Date(value.start_time);
    const end = new Date(value.end_time);
    if (Number.isNaN(start.getTime())) {
      ctx.addIssue({
        code: "custom",
        path: ["start_time"],
        message: "Enter a valid start time",
      });
    }
    if (Number.isNaN(end.getTime())) {
      ctx.addIssue({
        code: "custom",
        path: ["end_time"],
        message: "Enter a valid end time",
      });
    }
    if (
      !Number.isNaN(start.getTime()) &&
      !Number.isNaN(end.getTime()) &&
      end.getTime() <= start.getTime()
    ) {
      ctx.addIssue({
        code: "custom",
        path: ["end_time"],
        message: "End time must be after start time",
      });
    }
  });

const CancelSchema = z.object({
  cancellation_reason: z
    .string()
    .trim()
    .min(1, "Add a reason so customers know what happened")
    .max(500, "Reason must be 500 characters or fewer"),
});

function collectErrors<T extends string>(
  error: z.ZodError,
  keys: readonly T[],
): Partial<Record<T, string>> {
  const errors: Partial<Record<T, string>> = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (
      typeof key === "string" &&
      keys.includes(key as T) &&
      !errors[key as T]
    ) {
      errors[key as T] = issue.message;
    }
  }
  return errors;
}

export function parseOccurrenceEdit(input: OccurrenceEditFormValues): {
  data: OccurrenceUpdate | null;
  errors: EditErrorMap;
} {
  const result = EditSchema.safeParse(input);
  if (!result.success) {
    return {
      data: null,
      errors: collectErrors(result.error, [
        "title",
        "start_time",
        "end_time",
        "max_capacity",
      ]),
    };
  }
  return {
    data: {
      title: result.data.title,
      start_time: fromDatetimeLocalValue(result.data.start_time),
      end_time: fromDatetimeLocalValue(result.data.end_time),
      max_capacity: result.data.max_capacity,
    },
    errors: {},
  };
}

export function parseOccurrenceCancel(input: OccurrenceCancelFormValues): {
  data: OccurrenceUpdate | null;
  errors: CancelErrorMap;
} {
  const result = CancelSchema.safeParse(input);
  if (!result.success) {
    return {
      data: null,
      errors: collectErrors(result.error, ["cancellation_reason"]),
    };
  }
  return {
    data: {
      status: OccurrenceStatus.CANCELLED,
      cancellation_reason: result.data.cancellation_reason,
    },
    errors: {},
  };
}
