import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  createCourseBooking,
  createOrderCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
  getGuestOrderAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestOrderAccess,
} = vi.hoisted(() => ({
  createCourseBooking: vi.fn(),
  createOrderCheckoutSession: vi.fn(),
  createIdempotencyKey: vi.fn(() => "idem-order-1"),
  getUserFacingApiMessage: vi.fn(() => "Checkout failed"),
  getGuestOrderAccessToken: vi.fn(),
  getSafeStripeCheckoutUrl: vi.fn((url: string): string | null => url),
  storeGuestOrderAccess: vi.fn(),
}));

vi.mock("@shared/api", () => ({
  createCourseBooking,
  createOrderCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
}));

vi.mock("@shared/lib", () => ({
  getGuestOrderAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestOrderAccess,
}));

import { executeBookCourseCheckout } from "./execute-book-course-checkout";

const guest = {
  guest_name: "Ada",
  guest_email: "ada@example.com",
  guest_phone: "+353000",
};

describe("executeBookCourseCheckout", () => {
  const redirectTo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    createIdempotencyKey.mockReturnValue("idem-order-1");
    getSafeStripeCheckoutUrl.mockImplementation((url: string) => url);
  });

  it("creates a course order once then starts Stripe checkout", async () => {
    createCourseBooking.mockResolvedValue({
      order: {
        id: 42,
        service_id: 55,
        guest_name: "Ada",
        guest_email: "ada@example.com",
        status: "pending",
        total_amount_cents: 12000,
        currency: "eur",
      },
      bookings: [],
      access_token: "order-jwt",
    });
    createOrderCheckoutSession.mockResolvedValue({
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test",
    });

    const keys = new Map<number, string>();
    const result = await executeBookCourseCheckout({
      serviceId: 55,
      guest,
      heldOrderId: null,
      heldTotalAmountCents: null,
      checkoutKeyByOrder: keys,
      createKeyByIntent: new Map(),
      origin: "https://app.test",
      redirectTo,
    });

    expect(createCourseBooking).toHaveBeenCalledOnce();
    expect(storeGuestOrderAccess).toHaveBeenCalledWith(
      42,
      "order-jwt",
      expect.objectContaining({ id: 42, total_amount_cents: 12000 }),
    );
    expect(createOrderCheckoutSession).toHaveBeenCalledWith(
      expect.objectContaining({
        order_id: 42,
        access_token: "order-jwt",
        success_url: "https://app.test/bookings/success?order=42",
      }),
      { idempotencyKey: "idem-order-1" },
    );
    expect(redirectTo).toHaveBeenCalledWith(
      "https://checkout.stripe.com/c/pay/cs_test",
    );
    expect(result).toEqual({
      kind: "stripe",
      orderId: 42,
      totalAmountCents: 12000,
    });
    expect(keys.get(42)).toBe("idem-order-1");
  });

  it("skips create on retry and reuses held order + idempotency key", async () => {
    getGuestOrderAccessToken.mockReturnValue("stored-order-jwt");
    createOrderCheckoutSession.mockResolvedValue({
      checkout_url: "https://checkout.stripe.com/c/pay/cs_retry",
    });

    const keys = new Map<number, string>([[42, "idem-stable"]]);
    await executeBookCourseCheckout({
      serviceId: 55,
      guest,
      heldOrderId: 42,
      heldTotalAmountCents: 12000,
      checkoutKeyByOrder: keys,
      createKeyByIntent: new Map(),
      origin: "https://app.test",
      redirectTo,
    });

    expect(createCourseBooking).not.toHaveBeenCalled();
    expect(createOrderCheckoutSession).toHaveBeenCalledWith(
      expect.objectContaining({
        order_id: 42,
        access_token: "stored-order-jwt",
      }),
      { idempotencyKey: "idem-stable" },
    );
  });

  it("returns free when order total is zero", async () => {
    createCourseBooking.mockResolvedValue({
      order: {
        id: 7,
        service_id: 55,
        guest_name: "Ada",
        guest_email: "ada@example.com",
        status: "pending",
        total_amount_cents: 0,
        currency: "eur",
      },
      bookings: [],
      access_token: "free-order-jwt",
    });

    const result = await executeBookCourseCheckout({
      serviceId: 55,
      guest,
      heldOrderId: null,
      heldTotalAmountCents: null,
      checkoutKeyByOrder: new Map(),
      createKeyByIntent: new Map(),
      origin: "https://app.test",
      redirectTo,
    });

    expect(createOrderCheckoutSession).not.toHaveBeenCalled();
    expect(redirectTo).not.toHaveBeenCalled();
    expect(result).toEqual({
      kind: "free",
      orderId: 7,
      totalAmountCents: 0,
    });
  });

  it("returns checkout_failed when Stripe URL is unsafe", async () => {
    getGuestOrderAccessToken.mockReturnValue("guest-jwt");
    getSafeStripeCheckoutUrl.mockImplementation(() => null);
    createOrderCheckoutSession.mockResolvedValue({
      checkout_url: "https://evil.example/phish",
    });

    const result = await executeBookCourseCheckout({
      serviceId: 55,
      guest,
      heldOrderId: 42,
      heldTotalAmountCents: 12000,
      checkoutKeyByOrder: new Map(),
      createKeyByIntent: new Map(),
      origin: "https://app.test",
      redirectTo,
    });

    expect(result.kind).toBe("checkout_failed");
    expect(redirectTo).not.toHaveBeenCalled();
  });
});
