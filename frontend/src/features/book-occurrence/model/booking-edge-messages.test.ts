import { describe, expect, it } from "vitest";

import { ApiError } from "@shared/api";

import {
  getBookingCheckoutErrorMessage,
  isOccurrenceFullCheckoutError,
  OCCURRENCE_FULL_MESSAGE,
} from "./booking-edge-messages";

describe("booking edge messages", () => {
  it("detects capacity-full ValidationError from the API", () => {
    const error = new ApiError("Bad Request", 400, {
      detail: "No seats available",
    });
    expect(isOccurrenceFullCheckoutError(error)).toBe(true);
    expect(getBookingCheckoutErrorMessage(error)).toBe(OCCURRENCE_FULL_MESSAGE);
  });

  it("leaves unrelated errors unchanged", () => {
    const error = new ApiError("Conflict", 409, {
      detail: "You already have a booking for this session",
    });
    expect(isOccurrenceFullCheckoutError(error)).toBe(false);
    expect(getBookingCheckoutErrorMessage(error)).toBe(
      "You already have a booking for this session",
    );
  });
});
