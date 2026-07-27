import { describe, expect, it } from "vitest";

import {
  formatScheduleTemplateSummary,
  formatTemplateStartTime,
} from "./schedule-template";

describe("formatTemplateStartTime", () => {
  it("strips seconds from HH:MM:SS", () => {
    expect(formatTemplateStartTime("18:00:00")).toBe("18:00");
  });

  it("keeps HH:MM as-is with zero-padded hours", () => {
    expect(formatTemplateStartTime("9:30")).toBe("09:30");
  });
});

describe("formatScheduleTemplateSummary", () => {
  it("combines weekday label and start time", () => {
    expect(
      formatScheduleTemplateSummary({
        day_of_week: 1,
        start_time: "18:00:00",
      }),
    ).toBe("Tuesday at 18:00");
  });
});
