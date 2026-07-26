import { describe, expect, it, vi } from "vitest";

import {
  parseBookingRouteId,
  syncGuestAccessTokenFromQuery,
} from "./sync-guest-access-token";

describe("parseBookingRouteId", () => {
  it("accepts positive integers", () => {
    expect(parseBookingRouteId("42")).toBe(42);
    expect(parseBookingRouteId(7)).toBe(7);
  });

  it("rejects invalid ids", () => {
    expect(parseBookingRouteId("abc")).toBeNull();
    expect(parseBookingRouteId("0")).toBeNull();
    expect(parseBookingRouteId(-1)).toBeNull();
  });
});

describe("syncGuestAccessTokenFromQuery", () => {
  it("persists token and strips query param", () => {
    const persist = vi.fn();
    const replaceState = vi.fn();
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost/bookings/9/confirm?access_token=secret&x=1",
      },
      history: { replaceState },
    });

    syncGuestAccessTokenFromQuery(9, "secret", persist);

    expect(persist).toHaveBeenCalledWith(9, "secret");
    expect(replaceState).toHaveBeenCalledWith(
      {},
      "",
      "/bookings/9/confirm?x=1",
    );

    vi.unstubAllGlobals();
  });

  it("no-ops when query token is missing", () => {
    const persist = vi.fn();
    syncGuestAccessTokenFromQuery(9, null, persist);
    expect(persist).not.toHaveBeenCalled();
  });
});
