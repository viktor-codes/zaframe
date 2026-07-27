import { z } from "zod";

export const GuestDetailsSchema = z.object({
  guest_name: z.string().trim().min(1, "Enter your name"),
  guest_email: z.string().trim().pipe(z.email("Enter a valid email")),
  guest_phone: z
    .string()
    .trim()
    .optional()
    .transform((value) => (value && value.length > 0 ? value : undefined)),
});

export type GuestDetails = z.infer<typeof GuestDetailsSchema>;

export function parseGuestDetails(input: {
  guest_name: string;
  guest_email: string;
  guest_phone: string;
}): {
  data: GuestDetails;
  errors: Partial<Record<keyof GuestDetails, string>>;
} {
  const result = GuestDetailsSchema.safeParse(input);
  if (result.success) {
    return { data: result.data, errors: {} };
  }

  const errors: Partial<Record<keyof GuestDetails, string>> = {};
  for (const issue of result.error.issues) {
    const key = issue.path[0];
    if (
      (key === "guest_name" ||
        key === "guest_email" ||
        key === "guest_phone") &&
      !errors[key]
    ) {
      errors[key] = issue.message;
    }
  }

  return {
    data: {
      guest_name: input.guest_name,
      guest_email: input.guest_email,
      guest_phone: input.guest_phone.trim() || undefined,
    },
    errors,
  };
}
