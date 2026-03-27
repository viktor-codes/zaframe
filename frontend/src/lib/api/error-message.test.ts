import { describe, expect, it } from "vitest";

import { ApiError } from "./client";
import { getUserFacingApiMessage } from "./error-message";

describe("getUserFacingApiMessage", () => {
  it("uses validation detail from Problem JSON body for ApiError", () => {
    const err = new ApiError("Unprocessable Entity", 422, {
      detail: [{ msg: "Email is required", loc: ["body", "email"] }],
    });
    expect(getUserFacingApiMessage(err)).toContain("Email is required");
  });

  it("maps ApiError status to default copy when body is empty", () => {
    expect(getUserFacingApiMessage(new ApiError("x", 401))).toBe(
      "Please sign in to continue.",
    );
    expect(getUserFacingApiMessage(new ApiError("x", 500))).toBe(
      "Something went wrong on our side. Please try again later.",
    );
  });

  it("maps network-style ApiError messages to network copy", () => {
    expect(getUserFacingApiMessage(new ApiError("Failed to fetch", 0))).toBe(
      "Network error. Check your connection and try again.",
    );
  });

  it("shows short safe Error messages", () => {
    expect(getUserFacingApiMessage(new Error("Invalid email"))).toBe(
      "Invalid email",
    );
  });

  it("hides verbose or technical Error messages", () => {
    expect(
      getUserFacingApiMessage(
        new Error(
          "Minified React error #418; visit https://react.dev/errors/418",
        ),
      ),
    ).toBe("Something went wrong. Please try again.");
    expect(
      getUserFacingApiMessage(
        new Error("Error: boom\n  at foo (/app/src/x.ts:12:34)"),
      ),
    ).toBe("Something went wrong. Please try again.");
  });

  it("maps generic network Error instances to network copy", () => {
    expect(getUserFacingApiMessage(new Error("Failed to fetch"))).toBe(
      "Network error. Check your connection and try again.",
    );
  });

  it("returns generic copy for non-Error unknown", () => {
    expect(getUserFacingApiMessage("oops")).toBe(
      "Something went wrong. Please try again.",
    );
  });
});
