import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import {
  createCheckoutSession,
  createOrderCheckoutSession,
} from "./payments";
import { setAuthTokenProvider } from "./client";

describe("createCheckoutSession", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("sends session Bearer when there is no guest access_token", async () => {
    const fetchMock = vi.fn(async (_input: string | URL, init?: RequestInit) => {
      return new Response(
        JSON.stringify({ checkout_url: "https://stripe.test/c", session_id: "cs_1" }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    await createCheckoutSession(
      {
        booking_id: 1,
        success_url: "https://app.test/ok",
        cancel_url: "https://app.test/cancel",
      },
      { idempotencyKey: "idem-session-1" },
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
    expect(headers.get("Idempotency-Key")).toBe("idem-session-1");
  });

  it("skips session Bearer for guest checkout with access_token", async () => {
    const fetchMock = vi.fn(async (_input: string | URL, init?: RequestInit) => {
      return new Response(
        JSON.stringify({ checkout_url: "https://stripe.test/c", session_id: "cs_1" }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    await createCheckoutSession(
      {
        booking_id: 1,
        success_url: "https://app.test/ok",
        cancel_url: "https://app.test/cancel",
        access_token: "guest-jwt",
      },
      { idempotencyKey: "idem-guest-1" },
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBeNull();
    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(body.access_token).toBe("guest-jwt");
  });
});

describe("createOrderCheckoutSession", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts to order-checkout-session with Idempotency-Key", async () => {
    const fetchMock = vi.fn(
      async (_input: string | URL, _init?: RequestInit) => {
        expect(String(_input)).toContain(
          "/api/v1/payments/order-checkout-session",
        );
        return new Response(
          JSON.stringify({
            checkout_url: "https://stripe.test/o",
            session_id: "cs_o1",
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await createOrderCheckoutSession(
      {
        order_id: 42,
        success_url: "https://app.test/ok",
        cancel_url: "https://app.test/cancel",
      },
      { idempotencyKey: "idem-order-1" },
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
    expect(headers.get("Idempotency-Key")).toBe("idem-order-1");
    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(body.order_id).toBe(42);
  });

  it("skips session Bearer for guest order checkout with access_token", async () => {
    const fetchMock = vi.fn(
      async (_input: string | URL, _init?: RequestInit) => {
        return new Response(
          JSON.stringify({
            checkout_url: "https://stripe.test/o",
            session_id: "cs_o2",
          }),
          { status: 201, headers: { "Content-Type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);

    await createOrderCheckoutSession(
      {
        order_id: 7,
        success_url: "https://app.test/ok",
        cancel_url: "https://app.test/cancel",
        access_token: "order-guest-jwt",
      },
      { idempotencyKey: "idem-order-guest" },
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBeNull();
    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(body.access_token).toBe("order-guest-jwt");
  });
});
