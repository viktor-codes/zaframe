import { describe, expect, it } from "vitest";

import { groupOccurrencesByDate } from "./group-by-date";
import type { OccurrenceResponse } from "./types";

function localIso(
  year: number,
  month: number,
  day: number,
  hour: number,
  minute: number,
): string {
  return new Date(year, month - 1, day, hour, minute).toISOString();
}

function stubOccurrence(
  overrides: Partial<OccurrenceResponse> &
    Pick<OccurrenceResponse, "id" | "start_time" | "end_time" | "title">,
): OccurrenceResponse {
  return {
    studio_id: 1,
    service_id: 2,
    max_capacity: 10,
    price_cents: 0,
    status: "scheduled",
    created_at: "2026-07-01T00:00:00.000Z",
    updated_at: "2026-07-01T00:00:00.000Z",
    ...overrides,
  };
}

describe("groupOccurrencesByDate", () => {
  it("groups by local day and sorts within the day", () => {
    const groups = groupOccurrencesByDate([
      stubOccurrence({
        id: 2,
        title: "Evening",
        start_time: localIso(2026, 7, 27, 18, 0),
        end_time: localIso(2026, 7, 27, 19, 0),
      }),
      stubOccurrence({
        id: 1,
        title: "Morning",
        start_time: localIso(2026, 7, 27, 9, 0),
        end_time: localIso(2026, 7, 27, 10, 0),
      }),
      stubOccurrence({
        id: 3,
        title: "Next day",
        start_time: localIso(2026, 7, 28, 9, 0),
        end_time: localIso(2026, 7, 28, 10, 0),
      }),
    ]);

    expect(groups).toHaveLength(2);
    expect(groups[0].occurrences.map((item) => item.id)).toEqual([1, 2]);
    expect(groups[1].occurrences.map((item) => item.id)).toEqual([3]);
  });

  it("returns an empty list for no occurrences", () => {
    expect(groupOccurrencesByDate([])).toEqual([]);
  });
});
