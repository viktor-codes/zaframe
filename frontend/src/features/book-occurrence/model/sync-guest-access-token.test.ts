import { describe, expect, it, vi } from "vitest";

import {
  parseBookingRouteId,
  readAccessTokenFromHash,
  readGuestAccessTokenFromLocation,
  syncGuestAccessTokenFromLocation,
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
    expect(parseBookingRouteId("1.5")).toBeNull();
    expect(parseBookingRouteId("1e2")).toBeNull();
  });
});

describe("readAccessTokenFromHash", () => {
  it("parses access_token from hash", () => {
    expect(readAccessTokenFromHash("#access_token=secret")).toBe("secret");
    expect(readAccessTokenFromHash("#access_token=secret&x=1")).toBe("secret");
    expect(readAccessTokenFromHash("#x=1")).toBeNull();
    expect(readAccessTokenFromHash("")).toBeNull();
  });
});

describe("readGuestAccessTokenFromLocation", () => {
  it("prefers hash over query", () => {
    expect(
      readGuestAccessTokenFromLocation(
        "http://localhost/bookings/9/confirm?access_token=query",
        "#access_token=hash",
      ),
    ).toBe("hash");
  });

  it("falls back to query when hash is empty", () => {
    expect(
      readGuestAccessTokenFromLocation(
        "http://localhost/bookings/9/confirm?access_token=query",
        "",
      ),
    ).toBe("query");
  });
});

describe("syncGuestAccessTokenFromLocation", () => {
  it("persists hash token and strips hash", () => {
    const persist = vi.fn();
    const replaceState = vi.fn();
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost/bookings/9/confirm#access_token=secret",
        hash: "#access_token=secret",
      },
      history: { replaceState },
    });

    expect(syncGuestAccessTokenFromLocation(9, persist)).toBe("secret");
    expect(persist).toHaveBeenCalledWith(9, "secret");
    expect(replaceState).toHaveBeenCalledWith({}, "", "/bookings/9/confirm");

    vi.unstubAllGlobals();
  });

  it("persists legacy query token and strips query", () => {
    const persist = vi.fn();
    const replaceState = vi.fn();
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost/bookings/9/confirm?access_token=secret&x=1",
        hash: "",
      },
      history: { replaceState },
    });

    expect(syncGuestAccessTokenFromLocation(9, persist)).toBe("secret");
    expect(persist).toHaveBeenCalledWith(9, "secret");
    expect(replaceState).toHaveBeenCalledWith(
      {},
      "",
      "/bookings/9/confirm?x=1",
    );

    vi.unstubAllGlobals();
  });

  it("no-ops when token is missing", () => {
    const persist = vi.fn();
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost/bookings/9/confirm",
        hash: "",
      },
      history: { replaceState: vi.fn() },
    });

    expect(syncGuestAccessTokenFromLocation(9, persist)).toBeNull();
    expect(persist).not.toHaveBeenCalled();

    vi.unstubAllGlobals();
  });
});

describe("syncGuestAccessTokenFromQuery", () => {
  it("persists explicit query token and strips location", () => {
    const persist = vi.fn();
    const replaceState = vi.fn();
    vi.stubGlobal("window", {
      location: {
        href: "http://localhost/bookings/9/confirm?access_token=secret&x=1",
        hash: "",
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
});
