import { describe, expect, it } from "vitest";

import {
  DAY_OF_WEEK,
  getDayOfWeekLabel,
  getDayOfWeekShortLabel,
  isDayOfWeek,
} from "./day-of-week";

describe("day-of-week", () => {
  it("treats 0 as Monday per API contract", () => {
    expect(getDayOfWeekLabel(DAY_OF_WEEK.MONDAY)).toBe("Monday");
    expect(getDayOfWeekShortLabel(0)).toBe("Mon");
  });

  it("treats 6 as Sunday", () => {
    expect(getDayOfWeekLabel(DAY_OF_WEEK.SUNDAY)).toBe("Sunday");
    expect(isDayOfWeek(6)).toBe(true);
  });

  it("rejects out-of-range values", () => {
    expect(isDayOfWeek(-1)).toBe(false);
    expect(isDayOfWeek(7)).toBe(false);
    expect(getDayOfWeekLabel(9)).toBe("Day 9");
  });
});
