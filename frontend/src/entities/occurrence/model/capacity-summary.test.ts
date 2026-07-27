import { describe, expect, it } from "vitest";

import { summarizeOccurrenceCapacity } from "./capacity-summary";

describe("summarizeOccurrenceCapacity", () => {
  it("sums confirmed, pending, and max capacity across sessions", () => {
    const summary = summarizeOccurrenceCapacity([
      { max_capacity: 10, confirmed_count: 3, pending_count: 1 },
      { max_capacity: 8, confirmed_count: 2, pending_count: 0 },
    ]);

    expect(summary).toEqual({
      sessionCount: 2,
      confirmedCount: 5,
      pendingCount: 1,
      maxCapacity: 18,
      heldSeats: 6,
    });
  });

  it("treats nullish counts as zero", () => {
    const summary = summarizeOccurrenceCapacity([
      { max_capacity: 5, confirmed_count: null, pending_count: undefined },
    ]);

    expect(summary).toEqual({
      sessionCount: 1,
      confirmedCount: 0,
      pendingCount: 0,
      maxCapacity: 5,
      heldSeats: 0,
    });
  });

  it("returns zeros for an empty list", () => {
    expect(summarizeOccurrenceCapacity([])).toEqual({
      sessionCount: 0,
      confirmedCount: 0,
      pendingCount: 0,
      maxCapacity: 0,
      heldSeats: 0,
    });
  });
});
