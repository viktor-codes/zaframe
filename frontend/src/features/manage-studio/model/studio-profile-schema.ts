import { z } from "zod";

import type { StudioCreate, StudioUpdate } from "@entities/studio";

import {
  emptyStudioProfileForm,
  type StudioProfileFormValues,
} from "./studio-profile-form";

/** Mirror of backend `SLUG_PATTERN`. */
const SLUG_PATTERN = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const emptyToNull = (max: number, message: string) =>
  z
    .string()
    .trim()
    .max(max, message)
    .transform((value) => (value.length > 0 ? value : null));

const optionalEmail = z
  .string()
  .trim()
  .max(254, "Email is too long")
  .transform((value) => (value.length > 0 ? value : null))
  .pipe(z.union([z.email("Enter a valid email"), z.null()]));

const optionalSlug = z
  .string()
  .trim()
  .toLowerCase()
  .max(255, "Slug must be 255 characters or fewer")
  .refine((value) => value.length === 0 || SLUG_PATTERN.test(value), {
    message: "Use lowercase letters, numbers, and single hyphens",
  })
  .transform((value) => (value.length > 0 ? value : null));

const requiredSlug = z
  .string()
  .trim()
  .toLowerCase()
  .min(1, "Add a public slug")
  .max(255, "Slug must be 255 characters or fewer")
  .regex(SLUG_PATTERN, "Use lowercase letters, numbers, and single hyphens");

const cancelBeforeHours = z.coerce
  .number({ error: "Enter cancellation cutoff in hours" })
  .int("Use a whole number of hours")
  .min(0, "Cutoff cannot be negative")
  .max(720, "Cutoff must be 720 hours or fewer");

const timezoneField = z
  .string()
  .trim()
  .min(1, "Choose a timezone")
  .max(64, "Timezone is too long");

const nameField = z
  .string()
  .trim()
  .min(1, "Enter a studio name")
  .max(200, "Name must be 200 characters or fewer");

const CreateStudioSchema = z.object({
  name: nameField,
  slug: optionalSlug,
  description: emptyToNull(5000, "Description is too long"),
  city: emptyToNull(100, "City must be 100 characters or fewer"),
  email: optionalEmail,
  phone: emptyToNull(20, "Phone must be 20 characters or fewer"),
  address: emptyToNull(500, "Address must be 500 characters or fewer"),
  timezone: timezoneField,
  cancel_before_hours: cancelBeforeHours,
});

const UpdateStudioSchema = z.object({
  name: nameField,
  slug: requiredSlug,
  description: z
    .string()
    .trim()
    .min(1, "Add a short description")
    .max(5000, "Description is too long"),
  city: z
    .string()
    .trim()
    .min(1, "Add a city")
    .max(100, "City must be 100 characters or fewer"),
  email: optionalEmail,
  phone: emptyToNull(20, "Phone must be 20 characters or fewer"),
  address: emptyToNull(500, "Address must be 500 characters or fewer"),
  timezone: timezoneField,
  cancel_before_hours: cancelBeforeHours,
});

type FormErrorMap = Partial<Record<keyof StudioProfileFormValues, string>>;

function collectErrors(error: z.ZodError): FormErrorMap {
  const errors: FormErrorMap = {};
  for (const issue of error.issues) {
    const key = issue.path[0];
    if (
      typeof key === "string" &&
      key in emptyStudioProfileForm() &&
      !errors[key as keyof StudioProfileFormValues]
    ) {
      errors[key as keyof StudioProfileFormValues] = issue.message;
    }
  }
  return errors;
}

export function parseCreateStudio(input: StudioProfileFormValues): {
  data: Omit<StudioCreate, "owner_id"> | null;
  errors: FormErrorMap;
} {
  const result = CreateStudioSchema.safeParse(input);
  if (!result.success) {
    return { data: null, errors: collectErrors(result.error) };
  }

  return { data: result.data, errors: {} };
}

export function parseUpdateStudio(input: StudioProfileFormValues): {
  data: StudioUpdate | null;
  errors: FormErrorMap;
} {
  const result = UpdateStudioSchema.safeParse(input);
  if (!result.success) {
    return { data: null, errors: collectErrors(result.error) };
  }

  return { data: result.data, errors: {} };
}

export type { StudioProfileFormValues };
export { emptyStudioProfileForm };
