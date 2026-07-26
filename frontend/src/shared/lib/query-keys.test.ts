import { describe, expect, it } from "vitest";

import { OccurrenceStatus } from "./constants";
import { queryKeys } from "./query-keys";

describe("queryKeys", () => {
  it("nests auth me under the auth prefix", () => {
    expect(queryKeys.auth.me(3)).toEqual(["auth", "me", 3]);
    expect(queryKeys.auth.me(3)[0]).toBe(queryKeys.auth.all[0]);
  });

  it("includes the full occurrence filters object in the key", () => {
    const filters = {
      status: OccurrenceStatus.SCHEDULED,
      size: 100,
      start_from: "2026-01-01T00:00:00.000Z",
    };
    expect(queryKeys.studio.occurrences(9, filters)).toEqual([
      "studio",
      9,
      "occurrences",
      filters,
    ]);
  });

  it("keys public service occurrences by slug and service id", () => {
    expect(queryKeys.studio.publicServiceOccurrences("yoga", 42)).toEqual([
      "studio",
      "slug",
      "yoga",
      "service",
      42,
      "occurrences",
    ]);
  });

  it("uses plural roots for list invalidation prefixes", () => {
    expect(queryKeys.studios.all).toEqual(["studios"]);
    expect(queryKeys.bookings.my()[0]).toBe("bookings");
  });
});
