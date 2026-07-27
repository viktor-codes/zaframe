import { describe, expect, it } from "vitest";

import {
  emptyAddMemberForm,
  parseAddMember,
} from "./member-form-schema";

describe("parseAddMember", () => {
  it("accepts a valid invite payload", () => {
    const parsed = parseAddMember({
      email: " coach@example.com ",
      role: "manager",
    });
    expect(parsed.errors).toEqual({});
    expect(parsed.data).toEqual({
      email: "coach@example.com",
      role: "manager",
    });
  });

  it("rejects empty and invalid email", () => {
    expect(parseAddMember(emptyAddMemberForm()).errors.email).toMatch(/email/i);
    expect(
      parseAddMember({ email: "not-an-email", role: "instructor" }).errors
        .email,
    ).toMatch(/incorrect/i);
  });
});
