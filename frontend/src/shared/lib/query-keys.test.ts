import { describe, expect, it } from "vitest";

import { queryKeys } from "./query-keys";

describe("queryKeys", () => {
  it("nests auth me under the auth prefix", () => {
    expect(queryKeys.auth.me(3)).toEqual(["auth", "me", 3]);
    expect(queryKeys.auth.me(3)[0]).toBe(queryKeys.auth.all[0]);
  });

  it("keeps studio detail and nested resources under studio id", () => {
    expect(queryKeys.studio.detail(9)).toEqual(["studio", 9]);
    expect(queryKeys.studio.services(9)).toEqual(["studio", 9, "services"]);
    expect(queryKeys.studio.occurrences(9, { status: "scheduled" })).toEqual([
      "studio",
      9,
      "occurrences",
      { status: "scheduled" },
    ]);
  });

  it("uses plural roots for list invalidation prefixes", () => {
    expect(queryKeys.studios.all).toEqual(["studios"]);
    expect(queryKeys.bookings.my()[0]).toBe("bookings");
  });
});
