import { describe, expect, it } from "vitest";

import { getOccurrenceBookActionLabel } from "./occurrence-action-label";

describe("getOccurrenceBookActionLabel", () => {
  it("returns No seats left when the occurrence is full", () => {
    expect(
      getOccurrenceBookActionLabel({ isFull: true, canBook: false }),
    ).toBe("No seats left");
  });

  it("returns Book when the occurrence is bookable", () => {
    expect(
      getOccurrenceBookActionLabel({ isFull: false, canBook: true }),
    ).toBe("Book");
  });

  it("returns Unavailable for non-full blocked slots", () => {
    expect(
      getOccurrenceBookActionLabel({ isFull: false, canBook: false }),
    ).toBe("Unavailable");
  });
});
