import { z } from "zod";
import type { CurrentUserUpdate } from "@entities/user";

export const ProfileUpdateSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Enter your name")
    .max(100, "Name must be 100 characters or fewer"),
  phone: z
    .string()
    .trim()
    .max(20, "Phone must be 20 characters or fewer")
    .transform((value) => (value.length > 0 ? value : null)),
  marketing_consent: z.boolean(),
});

export type ProfileUpdateForm = {
  name: string;
  phone: string;
  marketing_consent: boolean;
};

export type ProfileUpdateParsed = z.infer<typeof ProfileUpdateSchema>;

export function parseProfileUpdate(input: ProfileUpdateForm): {
  data: CurrentUserUpdate | null;
  errors: Partial<Record<keyof ProfileUpdateForm, string>>;
} {
  const result = ProfileUpdateSchema.safeParse(input);
  if (!result.success) {
    const errors: Partial<Record<keyof ProfileUpdateForm, string>> = {};
    for (const issue of result.error.issues) {
      const key = issue.path[0];
      if (
        (key === "name" || key === "phone" || key === "marketing_consent") &&
        !errors[key]
      ) {
        errors[key] = issue.message;
      }
    }
    return { data: null, errors };
  }

  return {
    data: {
      name: result.data.name,
      phone: result.data.phone,
      marketing_consent: result.data.marketing_consent,
    },
    errors: {},
  };
}
