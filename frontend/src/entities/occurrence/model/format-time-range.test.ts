import { describe, expect, it } from "vitest";

import { formatOccurrenceTimeRange } from "./format-time-range";

describe("formatOccurrenceTimeRange", () => {
  it("formats a local start–end time pair", () => {
    const start = new Date(2026, 6, 26, 9, 0, 0).toISOString();
    const end = new Date(2026, 6, 26, 10, 30, 0).toISOString();
    const label = formatOccurrenceTimeRange(start, end, "en-IE");
    expect(label).toContain("–");
    expect(label.length).toBeGreaterThan(5);
  });
});
