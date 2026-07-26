import { describe, expect, it } from "vitest";
import { parseProfileUpdate } from "./profile-schema";

describe("parseProfileUpdate", () => {
  it("accepts a valid profile and clears empty phone to null", () => {
    expect(
      parseProfileUpdate({
        name: " Ada Lovelace ",
        phone: "  ",
        marketing_consent: true,
      }),
    ).toEqual({
      data: {
        name: "Ada Lovelace",
        phone: null,
        marketing_consent: true,
      },
      errors: {},
    });
  });

  it("rejects an empty name", () => {
    const result = parseProfileUpdate({
      name: "   ",
      phone: "+353871234567",
      marketing_consent: false,
    });
    expect(result.data).toBeNull();
    expect(result.errors.name).toBe("Enter your name");
  });

  it("rejects a phone longer than 20 characters", () => {
    const result = parseProfileUpdate({
      name: "Ada",
      phone: "123456789012345678901",
      marketing_consent: false,
    });
    expect(result.data).toBeNull();
    expect(result.errors.phone).toMatch(/20/);
  });
});
