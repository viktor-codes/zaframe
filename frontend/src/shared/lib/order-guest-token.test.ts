import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";
import { QueryClient } from "@tanstack/react-query";

import {
  clearAllGuestOrderAccess,
  getGuestOrderAccessToken,
  getGuestOrderSnapshot,
  storeGuestOrderAccess,
} from "./order-guest-token";
import {
  clearAllGuestBookingAccess,
  getGuestBookingAccessToken,
  storeGuestBookingAccess,
} from "./booking-guest-token";
import { clearPrivateClientSession } from "./clear-private-client-session";
import { queryKeys } from "./query-keys";

function stubSessionStorage() {
  const store = new Map<string, string>();
  const sessionStorageMock = {
    get length() {
      return store.size;
    },
    key: (index: number) => [...store.keys()][index] ?? null,
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
    removeItem: (key: string) => {
      store.delete(key);
    },
  };
  vi.stubGlobal("window", { sessionStorage: sessionStorageMock });
  vi.stubGlobal("sessionStorage", sessionStorageMock);
  return store;
}

describe("order-guest-token", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("stores and reads guest order access + snapshot", () => {
    storeGuestOrderAccess(9, "order-jwt", {
      id: 9,
      service_id: 55,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      total_amount_cents: 12000,
      currency: "eur",
    });

    expect(getGuestOrderAccessToken(9)).toBe("order-jwt");
    expect(getGuestOrderSnapshot(9)).toEqual({
      id: 9,
      service_id: 55,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      total_amount_cents: 12000,
      currency: "eur",
    });
  });

  it("clears all guest order tokens and snapshots", () => {
    storeGuestOrderAccess(9, "order-jwt", {
      id: 9,
      service_id: 55,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      total_amount_cents: 12000,
      currency: "eur",
    });
    clearAllGuestOrderAccess();
    expect(getGuestOrderAccessToken(9)).toBeNull();
    expect(getGuestOrderSnapshot(9)).toBeNull();
  });
});

describe("booking-guest-token clear", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("clears all guest booking tokens and snapshots", () => {
    storeGuestBookingAccess(3, "booking-jwt", {
      id: 3,
      occurrence_id: 10,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      payment_status: null,
    });
    clearAllGuestBookingAccess();
    expect(getGuestBookingAccessToken(3)).toBeNull();
  });
});

describe("clearPrivateClientSession", () => {
  beforeEach(() => {
    stubSessionStorage();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("scrubs guest storage and private query caches", () => {
    storeGuestBookingAccess(3, "booking-jwt", {
      id: 3,
      occurrence_id: 10,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      payment_status: null,
    });
    storeGuestOrderAccess(9, "order-jwt", {
      id: 9,
      service_id: 55,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      total_amount_cents: 12000,
      currency: "eur",
    });

    const queryClient = new QueryClient();
    queryClient.setQueryData(queryKeys.auth.me(1), { id: 1 });
    queryClient.setQueryData(queryKeys.bookings.my(), [{ id: 3 }]);
    queryClient.setQueryData(queryKeys.booking.detail(3), { id: 3 });
    queryClient.setQueryData(queryKeys.orders.my(), [{ id: 9 }]);
    queryClient.setQueryData(queryKeys.order.detail(9), { id: 9 });
    queryClient.setQueryData(queryKeys.studios.explore({}), [{ id: 1 }]);

    clearPrivateClientSession(queryClient);

    expect(getGuestBookingAccessToken(3)).toBeNull();
    expect(getGuestOrderAccessToken(9)).toBeNull();
    expect(queryClient.getQueryData(queryKeys.auth.me(1))).toBeUndefined();
    expect(queryClient.getQueryData(queryKeys.bookings.my())).toBeUndefined();
    expect(queryClient.getQueryData(queryKeys.booking.detail(3))).toBeUndefined();
    expect(queryClient.getQueryData(queryKeys.orders.my())).toBeUndefined();
    expect(queryClient.getQueryData(queryKeys.order.detail(9))).toBeUndefined();
    expect(
      queryClient.getQueryData(queryKeys.studios.explore({})),
    ).toEqual([{ id: 1 }]);
  });
});
