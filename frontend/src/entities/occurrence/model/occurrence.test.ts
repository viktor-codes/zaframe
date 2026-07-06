import { describe, expect, it } from "vitest";
import { isOccurrenceBookable, isOccurrenceInPast } from "./occurrence";

describe("occurrence model", () => {
  const now = new Date("2026-07-06T12:00:00.000Z");

  it("detects past occurrences", () => {
    expect(
      isOccurrenceInPast({ start_time: "2026-07-06T11:00:00.000Z" }, now),
    ).toBe(true);
  });

  it("marks scheduled future occurrences as bookable", () => {
    expect(
      isOccurrenceBookable(
        {
          start_time: "2026-07-06T13:00:00.000Z",
          status: "scheduled",
        },
        now,
      ),
    ).toBe(true);
  });

  it("marks cancelled occurrences as not bookable", () => {
    expect(
      isOccurrenceBookable(
        {
          start_time: "2026-07-06T13:00:00.000Z",
          status: "cancelled",
        },
        now,
      ),
    ).toBe(false);
  });
});
