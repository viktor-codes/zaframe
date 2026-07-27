import { z } from "zod";

import {
  SERVICE_CATEGORIES,
  SERVICE_TYPE,
  type ServiceCreate,
  type ServiceUpdate,
} from "@entities/service";
import { ServiceVisibility } from "@shared/lib";
import {
  emptyServiceForm,
  eurosToCents,
  type ServiceFormValues,
} from "./service-form-values";

const positiveInt = (message: string) =>
  z.coerce.number({ error: message }).int(message).min(1, message);

const ServiceFormSchema = z
  .object({
    name: z.string().trim().min(1, "Enter a service name").max(200),
    description: z
      .string()
      .trim()
      .max(1000, "Description must be 1000 characters or fewer")
      .transform((value) => (value.length > 0 ? value : null)),
    type: z.enum([SERVICE_TYPE.SINGLE, SERVICE_TYPE.COURSE]),
    category: z.enum(SERVICE_CATEGORIES),
    duration_minutes: positiveInt("Duration must be at least 1 minute"),
    max_capacity: positiveInt("Capacity must be at least 1"),
    price_euros: z.string().trim().min(1, "Enter a drop-in price"),
    price_course_euros: z.string().trim(),
  })
  .superRefine((value, ctx) => {
    try {
      eurosToCents(value.price_euros);
    } catch {
      ctx.addIssue({
        code: "custom",
        path: ["price_euros"],
        message: "Enter a valid price (e.g. 25.00)",
      });
    }
    if (value.type !== SERVICE_TYPE.COURSE) return;
    if (!value.price_course_euros) {
      ctx.addIssue({
        code: "custom",
        path: ["price_course_euros"],
        message: "Enter a course price",
      });
      return;
    }
    try {
      eurosToCents(value.price_course_euros);
    } catch {
      ctx.addIssue({
        code: "custom",
        path: ["price_course_euros"],
        message: "Enter a valid course price",
      });
    }
  });

type FormErrorMap = Partial<Record<keyof ServiceFormValues, string>>;
type ParsedForm = z.infer<typeof ServiceFormSchema>;

function collectErrors(error: z.ZodError): FormErrorMap {
  const errors: FormErrorMap = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (
      typeof key === "string" &&
      key in emptyServiceForm() &&
      !errors[key as keyof ServiceFormValues]
    ) {
      errors[key as keyof ServiceFormValues] = issue.message;
    }
  }
  return errors;
}

function toServiceFields(value: ParsedForm) {
  return {
    name: value.name,
    description: value.description,
    type: value.type,
    category: value.category,
    duration_minutes: value.duration_minutes,
    max_capacity: value.max_capacity,
    price_single_cents: eurosToCents(value.price_euros),
    price_course_cents:
      value.type === SERVICE_TYPE.COURSE
        ? eurosToCents(value.price_course_euros)
        : null,
  };
}

export function parseCreateService(
  input: ServiceFormValues,
  studioId: number,
): { data: ServiceCreate | null; errors: FormErrorMap } {
  const result = ServiceFormSchema.safeParse(input);
  if (!result.success) {
    return { data: null, errors: collectErrors(result.error) };
  }
  return {
    data: {
      studio_id: studioId,
      ...toServiceFields(result.data),
      visibility: ServiceVisibility.DRAFT,
      tags: [],
      soft_limit_ratio: 1,
      hard_limit_ratio: 1.5,
      max_overbooked_ratio: 0.3,
    },
    errors: {},
  };
}

export function parseUpdateService(input: ServiceFormValues): {
  data: ServiceUpdate | null;
  errors: FormErrorMap;
} {
  const result = ServiceFormSchema.safeParse(input);
  if (!result.success) {
    return { data: null, errors: collectErrors(result.error) };
  }
  return { data: toServiceFields(result.data), errors: {} };
}
