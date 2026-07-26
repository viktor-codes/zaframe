import { describe, expect, it } from "vitest";

import {
  parseOccurrenceCancel,
  parseOccurrenceEdit,
} from "./occurrence-edit-schema";

describe("parseOccurrenceEdit", () => {
  it("converts local datetimes to ISO for the API", () => {
    const { data, errors } = parseOccurrenceEdit({
      title: "Morning Flow",
      start_time: "2026-07-27T10:00",
      end_time: "2026-07-27T11:00",
      max_capacity: "12",
    });

    expect(errors).toEqual({});
    expect(data?.title).toBe("Morning Flow");
    expect(data?.max_capacity).toBe(12);
    expect(data?.start_time).toMatch(/^\d{4}-\d{2}-\d{2}T/);
    expect(data?.end_time).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  it("rejects end before start", () => {
    const { data, errors } = parseOccurrenceEdit({
      title: "Morning Flow",
      start_time: "2026-07-27T11:00",
      end_time: "2026-07-27T10:00",
      max_capacity: "10",
    });

    expect(data).toBeNull();
    expect(errors.end_time).toBeTruthy();
  });
});

describe("parseOccurrenceCancel", () => {
  it("requires a cancellation reason", () => {
    const { data, errors } = parseOccurrenceCancel({
      cancellation_reason: "  ",
    });

    expect(data).toBeNull();
    expect(errors.cancellation_reason).toBeTruthy();
  });

  it("sets cancelled status with reason", () => {
    const { data, errors } = parseOccurrenceCancel({
      cancellation_reason: "Instructor sick",
    });

    expect(errors).toEqual({});
    expect(data).toEqual({
      status: "cancelled",
      cancellation_reason: "Instructor sick",
    });
  });
});
