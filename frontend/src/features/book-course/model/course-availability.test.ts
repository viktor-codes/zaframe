import { describe, expect, it } from "vitest";

import type { ServiceAvailabilityResponse } from "@entities/service";

import {
  COURSE_HARD_BLOCK_TITLE,
  COURSE_NO_SESSIONS_TITLE,
  COURSE_SOFT_WARNING_TITLE,
  formatCourseScheduleDate,
  getCourseAvailabilityPresentation,
  getScheduleRowCapacityLabel,
} from "./course-availability";

function availability(
  overrides: Partial<ServiceAvailabilityResponse> = {},
): ServiceAvailabilityResponse {
  return {
    service_id: 1,
    can_book: true,
    requires_warning: false,
    warning_message: null,
    schedule_details: [],
    ...overrides,
  };
}

describe("getCourseAvailabilityPresentation", () => {
  it("blocks when can_book is false and schedule is empty", () => {
    const result = getCourseAvailabilityPresentation(
      availability({ can_book: false, schedule_details: [] }),
    );
    expect(result.tone).toBe("blocked");
    expect(result.canProceed).toBe(false);
    expect(result.title).toBe(COURSE_NO_SESSIONS_TITLE);
  });

  it("blocks with hard-capacity copy when schedule has overbooked dates", () => {
    const result = getCourseAvailabilityPresentation(
      availability({
        can_book: false,
        schedule_details: [
          { date: "2026-08-01", is_overbooked: true, remaining: 0 },
        ],
      }),
    );
    expect(result.tone).toBe("blocked");
    expect(result.title).toBe(COURSE_HARD_BLOCK_TITLE);
    expect(result.overbookedCount).toBe(1);
  });

  it("warns when requires_warning and prefers API message", () => {
    const result = getCourseAvailabilityPresentation(
      availability({
        requires_warning: true,
        warning_message:
          "Some course sessions will be fuller, but booking is still allowed.",
        schedule_details: [
          { date: "2026-08-01", is_overbooked: true, remaining: 1 },
          { date: "2026-08-08", is_overbooked: false, remaining: 5 },
        ],
      }),
    );
    expect(result.tone).toBe("warning");
    expect(result.canProceed).toBe(true);
    expect(result.title).toBe(COURSE_SOFT_WARNING_TITLE);
    expect(result.message).toContain("fuller");
    expect(result.overbookedCount).toBe(1);
  });

  it("returns ok tone when no warning", () => {
    const result = getCourseAvailabilityPresentation(
      availability({
        schedule_details: [
          { date: "2026-08-01", is_overbooked: false, remaining: 4 },
        ],
      }),
    );
    expect(result.tone).toBe("ok");
    expect(result.canProceed).toBe(true);
    expect(result.title).toBe("");
  });
});

describe("formatCourseScheduleDate", () => {
  it("formats YYYY-MM-DD without shifting the calendar day", () => {
    expect(formatCourseScheduleDate("2026-08-01")).toMatch(/1.*Aug/i);
  });
});

describe("getScheduleRowCapacityLabel", () => {
  it("labels hard limit and zero remaining as Full", () => {
    expect(
      getScheduleRowCapacityLabel({
        date: "2026-08-01",
        is_overbooked: true,
        remaining: 0,
        overbooking_status: "HARD_LIMIT_REACHED",
      }),
    ).toBe("Full");
  });

  it("labels soft overbook as Limited", () => {
    expect(
      getScheduleRowCapacityLabel({
        date: "2026-08-01",
        is_overbooked: true,
        remaining: 1,
        overbooking_status: "SOFT_LIMIT_REACHED",
      }),
    ).toBe("Limited");
  });

  it("shows seat counts when not overbooked", () => {
    expect(
      getScheduleRowCapacityLabel({
        date: "2026-08-01",
        is_overbooked: false,
        remaining: 1,
      }),
    ).toBe("1 seat left");
    expect(
      getScheduleRowCapacityLabel({
        date: "2026-08-01",
        is_overbooked: false,
        remaining: 4,
      }),
    ).toBe("4 seats left");
  });
});
