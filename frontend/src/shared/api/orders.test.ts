import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import { setAuthTokenProvider } from "./client";
import { fetchOrder } from "./orders";

describe("fetchOrder", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("sends session Bearer when there is no guest access token", async () => {
    const fetchMock = vi.fn(
      async (_input: string | URL, _init?: RequestInit) => {
        expect(String(_input)).toContain("/api/v1/orders/42");
        return new Response(
          JSON.stringify({
            id: 42,
            status: "pending",
            total_amount_cents: 12000,
            currency: "eur",
            studio_id: 1,
            service_id: 55,
            user_id: null,
            guest_email: "ada@example.com",
            guest_name: "Ada",
            created_at: "2026-07-27T00:00:00Z",
            updated_at: "2026-07-27T00:00:00Z",
            bookings: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchOrder(42);

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
  });

  it("sends guest opaque token as Bearer and skips session auth", async () => {
    const fetchMock = vi.fn(
      async (_input: string | URL, _init?: RequestInit) => {
        return new Response(
          JSON.stringify({
            id: 7,
            status: "pending",
            total_amount_cents: 8000,
            currency: "eur",
            studio_id: 1,
            service_id: 55,
            user_id: null,
            guest_email: "ada@example.com",
            guest_name: "Ada",
            created_at: "2026-07-27T00:00:00Z",
            updated_at: "2026-07-27T00:00:00Z",
            bookings: [],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await fetchOrder(7, { accessToken: "order-guest-jwt" });

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer order-guest-jwt");
  });
});
