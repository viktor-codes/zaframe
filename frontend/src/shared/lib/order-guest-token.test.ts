import { describe, expect, it, beforeEach, afterEach, vi } from "vitest";

import {
  getGuestOrderAccessToken,
  getGuestOrderSnapshot,
  storeGuestOrderAccess,
} from "./order-guest-token";

describe("order-guest-token", () => {
  beforeEach(() => {
    const store = new Map<string, string>();
    const sessionStorageMock = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => {
        store.set(key, value);
      },
      removeItem: (key: string) => {
        store.delete(key);
      },
    };
    // WHY: module guards on `window`; Vitest node env has none by default.
    vi.stubGlobal("window", { sessionStorage: sessionStorageMock });
    vi.stubGlobal("sessionStorage", sessionStorageMock);
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
});
