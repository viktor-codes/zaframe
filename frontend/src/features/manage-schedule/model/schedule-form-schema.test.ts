import { describe, expect, it } from "vitest";

import {
  parseCreateTemplate,
  parseGenerateOccurrences,
} from "./schedule-form-schema";
import { emptyGenerateForm, emptyTemplateForm } from "./schedule-form-values";

describe("parseCreateTemplate", () => {
  it("normalises start_time to HH:MM:SS", () => {
    const { data, errors } = parseCreateTemplate(
      emptyTemplateForm({
        day_of_week: "1",
        start_time: "18:00",
        valid_from: "2026-07-26",
      }),
    );

    expect(errors).toEqual({});
    expect(data).toMatchObject({
      day_of_week: 1,
      start_time: "18:00:00",
      valid_from: "2026-07-26",
      valid_to: null,
    });
  });

  it("rejects end date before start date", () => {
    const { data, errors } = parseCreateTemplate(
      emptyTemplateForm({
        valid_from: "2026-08-01",
        valid_to: "2026-07-01",
      }),
    );

    expect(data).toBeNull();
    expect(errors.valid_to).toBeTruthy();
  });
});

describe("parseGenerateOccurrences", () => {
  it("builds a generate request for the service", () => {
    const { data, errors } = parseGenerateOccurrences(
      emptyGenerateForm({
        days: ["1", "3"],
        start_time: "09:30",
        weeks_count: "4",
      }),
      42,
    );

    expect(errors).toEqual({});
    expect(data).toEqual({
      service_id: 42,
      days: [1, 3],
      start_time: "09:30:00",
      weeks_count: 4,
    });
  });

  it("requires at least one day", () => {
    const { data, errors } = parseGenerateOccurrences(
      emptyGenerateForm({ days: [] }),
      42,
    );

    expect(data).toBeNull();
    expect(errors.days).toBeTruthy();
  });
});
