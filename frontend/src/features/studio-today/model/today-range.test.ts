import { describe, expect, it } from "vitest";

import { buildTodayParams, formatTodayHeading, TODAY_PAGE_SIZE } from "./today-range";

describe("buildTodayParams", () => {
  it("requests scheduled sessions from local midnight to next midnight", () => {
    const now = new Date(2026, 6, 26, 15, 30, 0);
    const params = buildTodayParams(now);

    const start = new Date(2026, 6, 26, 0, 0, 0, 0);
    const end = new Date(2026, 6, 27, 0, 0, 0, 0);

    expect(params).toEqual({
      start_from: start.toISOString(),
      start_to: end.toISOString(),
      status: "scheduled",
      size: TODAY_PAGE_SIZE,
    });
  });
});

describe("formatTodayHeading", () => {
  it("formats a readable local day label", () => {
    const now = new Date(2026, 6, 26, 9, 0, 0);
    expect(formatTodayHeading(now, "en-IE")).toMatch(/26/);
    expect(formatTodayHeading(now, "en-IE")).toMatch(/July/i);
  });
});
