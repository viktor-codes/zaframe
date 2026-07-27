import { describe, expect, it } from "vitest";

import {
  canMutateStudioMemberRole,
  formatStudioMemberRole,
} from "./member-role";

describe("member role helpers", () => {
  it("blocks mutate actions for owners", () => {
    expect(canMutateStudioMemberRole("owner")).toBe(false);
    expect(canMutateStudioMemberRole("manager")).toBe(true);
    expect(canMutateStudioMemberRole("instructor")).toBe(true);
  });

  it("formats known roles for display", () => {
    expect(formatStudioMemberRole("owner")).toBe("Owner");
    expect(formatStudioMemberRole("manager")).toBe("Manager");
    expect(formatStudioMemberRole("instructor")).toBe("Instructor");
  });
});
