import { describe, expect, it } from "vitest";

import { OccurrenceStatus } from "./constants";
import { queryKeys } from "./query-keys";

describe("queryKeys", () => {
  it("nests auth me under the auth prefix", () => {
    expect(queryKeys.auth.me(3)).toEqual(["auth", "me", 3]);
    expect(queryKeys.auth.me(3)[0]).toBe(queryKeys.auth.all[0]);
  });

  it("nests occurrence filters under occurrencesRoot", () => {
    const filters = {
      status: OccurrenceStatus.SCHEDULED,
      size: 100,
      start_from: "2026-01-01T00:00:00.000Z",
    };
    expect(queryKeys.studio.occurrencesRoot(9)).toEqual([
      "studio",
      9,
      "occurrences",
    ]);
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

  it("keys my-studios membership list under the studios prefix", () => {
    expect(queryKeys.studios.my).toEqual(["studios", "my"]);
    expect(queryKeys.studios.my[0]).toBe(queryKeys.studios.all[0]);
  });

  it("includes my-bookings list filters in the key", () => {
    const params = { size: 20, include_guest_email: true };
    expect(queryKeys.bookings.my(params)).toEqual(["bookings", "my", params]);
  });

  it("includes studio bookings filters in the key", () => {
    const filters = { studio_id: 9, status: "pending" as const, size: 20 };
    expect(queryKeys.studio.bookings(9, filters)).toEqual([
      "studio",
      9,
      "bookings",
      filters,
    ]);
  });

  it("nests studio services filters under servicesRoot", () => {
    const filters = { size: 20 };
    expect(queryKeys.studio.servicesRoot(9)).toEqual([
      "studio",
      9,
      "services",
    ]);
    expect(queryKeys.studio.services(9, filters)).toEqual([
      "studio",
      9,
      "services",
      filters,
    ]);
    expect(queryKeys.studio.services(9, filters)[0]).toBe(
      queryKeys.studio.servicesRoot(9)[0],
    );
  });

  it("includes my-orders list filters in the key", () => {
    const params = { size: 20 };
    expect(queryKeys.orders.my(params)).toEqual(["orders", "my", params]);
  });

  it("keys order detail by id", () => {
    expect(queryKeys.order.detail(42)).toEqual(["order", 42]);
  });

  it("keys service availability by id and optional start date", () => {
    expect(queryKeys.service.availability(55)).toEqual([
      "service",
      55,
      "availability",
      null,
    ]);
    expect(queryKeys.service.availability(55, "2026-08-01")).toEqual([
      "service",
      55,
      "availability",
      "2026-08-01",
    ]);
  });
});

