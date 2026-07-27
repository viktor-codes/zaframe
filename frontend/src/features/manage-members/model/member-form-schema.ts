import { z } from "zod";

import type { StudioMemberCreate } from "@entities/studio";

export const ASSIGNABLE_MEMBER_ROLES = ["manager", "instructor"] as const;

export type AssignableMemberRole = (typeof ASSIGNABLE_MEMBER_ROLES)[number];

export const AddMemberSchema = z.object({
  email: z
    .string()
    .trim()
    .min(1, "Enter an email")
    .email("Email address looks incorrect"),
  role: z.enum(ASSIGNABLE_MEMBER_ROLES),
});

export type AddMemberForm = {
  email: string;
  role: AssignableMemberRole;
};

export function emptyAddMemberForm(): AddMemberForm {
  return { email: "", role: "instructor" };
}

export function parseAddMember(input: AddMemberForm): {
  data: StudioMemberCreate | null;
  errors: Partial<Record<keyof AddMemberForm, string>>;
} {
  const result = AddMemberSchema.safeParse(input);
  if (!result.success) {
    const errors: Partial<Record<keyof AddMemberForm, string>> = {};
    for (const issue of result.error.issues) {
      const key = issue.path[0];
      if ((key === "email" || key === "role") && !errors[key]) {
        errors[key] = issue.message;
      }
    }
    return { data: null, errors };
  }

  return {
    data: {
      email: result.data.email,
      role: result.data.role,
    },
    errors: {},
  };
}
