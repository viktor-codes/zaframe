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
  createStudioStripeOnboarding,
  fetchStudioPayoutSettings,
  fetchStudioStripeStatus,
  updateStudioPayoutSettings,
} from "./payments";
import { setAuthTokenProvider } from "./client";

const connectStatusPayload = {
  studio_id: 7,
  stripe_account_id: "acct_1",
  stripe_charges_enabled: false,
  stripe_payouts_enabled: false,
  stripe_onboarding_completed_at: null,
  stripe_onboarding_url_expires_at: null,
};

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

describe("studio Stripe Connect API", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("fetches studio stripe status with Bearer", async () => {
    const fetchMock = vi.fn(async (input: string | URL) => {
      expect(String(input)).toContain("/api/v1/studios/7/stripe/status");
      return new Response(JSON.stringify(connectStatusPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchStudioStripeStatus(7);

    expect(result.studio_id).toBe(7);
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
  });

  it("posts stripe onboard with return and refresh URLs", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      expect(String(input)).toContain("/api/v1/studios/7/stripe/onboard");
      expect(init?.method).toBe("POST");
      return new Response(
        JSON.stringify({
          ...connectStatusPayload,
          onboarding_url: "https://connect.stripe.com/setup/e/acct_1",
        }),
        { status: 201, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await createStudioStripeOnboarding(7, {
      return_url: "https://app.test/dashboard/studios/7/payouts",
      refresh_url: "https://app.test/dashboard/studios/7/payouts",
    });

    expect(result.onboarding_url).toContain("connect.stripe.com");
    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(body.return_url).toContain("/payouts");
    expect(body.refresh_url).toContain("/payouts");
  });

  it("fetches and patches payout settings", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      expect(String(input)).toContain("/api/v1/studios/7/payout-settings");
      if (init?.method === "PATCH") {
        const body = JSON.parse(String(init.body));
        expect(body.refresh_from_stripe).toBe(true);
        return new Response(
          JSON.stringify({
            ...connectStatusPayload,
            stripe_charges_enabled: true,
            stripe_payouts_enabled: true,
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }
      return new Response(JSON.stringify(connectStatusPayload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchStudioPayoutSettings(7);
    const refreshed = await updateStudioPayoutSettings(7, {
      refresh_from_stripe: true,
    });

    expect(refreshed.stripe_charges_enabled).toBe(true);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
