import { describe, expect, it } from "vitest";
import { parseGuestDetails } from "./guest-details-schema";

describe("parseGuestDetails", () => {
  it("accepts a valid guest payload", () => {
    const { data, errors } = parseGuestDetails({
      guest_name: " Ada Lovelace ",
      guest_email: "ada@example.com",
      guest_phone: "",
    });

    expect(errors).toEqual({});
    expect(data.guest_name).toBe("Ada Lovelace");
    expect(data.guest_email).toBe("ada@example.com");
    expect(data.guest_phone).toBeUndefined();
  });

  it("rejects an empty name and invalid email", () => {
    const { errors } = parseGuestDetails({
      guest_name: "   ",
      guest_email: "not-an-email",
      guest_phone: "",
    });

    expect(errors.guest_name).toBeTruthy();
    expect(errors.guest_email).toBeTruthy();
  });
});
