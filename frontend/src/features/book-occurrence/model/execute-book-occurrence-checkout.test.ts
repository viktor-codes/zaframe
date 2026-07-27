import { beforeEach, describe, expect, it, vi } from "vitest";

const {
  createBooking,
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
  getGuestBookingAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestBookingAccess,
} = vi.hoisted(() => ({
  createBooking: vi.fn(),
  createCheckoutSession: vi.fn(),
  createIdempotencyKey: vi.fn(() => "idem-key-1"),
  getUserFacingApiMessage: vi.fn(() => "Checkout failed"),
  getGuestBookingAccessToken: vi.fn(),
  getSafeStripeCheckoutUrl: vi.fn((url: string) => url),
  storeGuestBookingAccess: vi.fn(),
}));

vi.mock("@shared/api", () => ({
  createBooking,
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
}));

vi.mock("@shared/lib", () => ({
  getGuestBookingAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestBookingAccess,
}));

import { executeBookOccurrenceCheckout } from "./execute-book-occurrence-checkout";
import type { OccurrenceResponse } from "@entities/occurrence";

const occurrence = {
  id: 10,
  service_id: 3,
  price_cents: 2500,
  title: "Morning flow",
  start_time: "2026-07-28T09:00:00Z",
} as OccurrenceResponse;

const guest = {
  guest_name: "Ada",
  guest_email: "ada@example.com",
  guest_phone: "+353000",
};

describe("executeBookOccurrenceCheckout", () => {
  const redirectTo = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    createIdempotencyKey.mockReturnValue("idem-key-1");
    getSafeStripeCheckoutUrl.mockImplementation((url: string) => url);
  });

  it("creates a booking once then starts Stripe checkout", async () => {
    createBooking.mockResolvedValue({
      id: 42,
      occurrence_id: 10,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      payment_status: "unpaid",
      reserved_until: null,
      access_token: "guest-jwt",
    });
    createCheckoutSession.mockResolvedValue({
      checkout_url: "https://checkout.stripe.com/c/pay/cs_test",
    });

    const keys = new Map<number, string>();
    const result = await executeBookOccurrenceCheckout({
      occurrence,
      guest,
      heldBookingId: null,
      checkoutKeyByBooking: keys,
      createKeyByIntent: new Map(),
      origin: "http://localhost",
      redirectTo,
    });

    expect(createBooking).toHaveBeenCalledOnce();
    expect(createBooking).toHaveBeenCalledWith(
      expect.objectContaining({ occurrence_id: 10 }),
      { idempotencyKey: "idem-key-1" },
    );
    expect(createCheckoutSession).toHaveBeenCalledWith(
      expect.objectContaining({
        booking_id: 42,
        access_token: "guest-jwt",
      }),
      { idempotencyKey: "idem-key-1" },
    );
    expect(keys.get(42)).toBe("idem-key-1");
    expect(redirectTo).toHaveBeenCalledWith(
      "https://checkout.stripe.com/c/pay/cs_test",
    );
    expect(result).toEqual({ kind: "stripe", bookingId: 42 });
  });

  it("retries checkout without createBooking when a hold already exists", async () => {
    getGuestBookingAccessToken.mockReturnValue("stored-jwt");
    createCheckoutSession.mockResolvedValue({
      checkout_url: "https://checkout.stripe.com/c/pay/cs_retry",
    });

    const keys = new Map<number, string>([[42, "idem-key-held"]]);
    const result = await executeBookOccurrenceCheckout({
      occurrence,
      guest,
      heldBookingId: 42,
      checkoutKeyByBooking: keys,
      createKeyByIntent: new Map(),
      origin: "http://localhost",
      redirectTo,
    });

    expect(createBooking).not.toHaveBeenCalled();
    expect(createCheckoutSession).toHaveBeenCalledWith(
      expect.objectContaining({
        booking_id: 42,
        access_token: "stored-jwt",
      }),
      { idempotencyKey: "idem-key-held" },
    );
    expect(createIdempotencyKey).not.toHaveBeenCalled();
    expect(result).toEqual({ kind: "stripe", bookingId: 42 });
  });

  it("reuses the same Idempotency-Key for the same booking on checkout_failed retry", async () => {
    createBooking.mockResolvedValue({
      id: 7,
      occurrence_id: 10,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      status: "pending",
      payment_status: "unpaid",
      reserved_until: null,
      access_token: "guest-jwt",
    });
    createCheckoutSession.mockRejectedValue(new Error("stripe down"));

    const keys = new Map<number, string>();
    const first = await executeBookOccurrenceCheckout({
      occurrence,
      guest,
      heldBookingId: null,
      checkoutKeyByBooking: keys,
      createKeyByIntent: new Map(),
      origin: "http://localhost",
      redirectTo,
    });
    expect(first.kind).toBe("checkout_failed");
    expect(keys.get(7)).toBe("idem-key-1");

    getGuestBookingAccessToken.mockReturnValue("guest-jwt");
    createIdempotencyKey.mockReturnValue("idem-key-2");
    createCheckoutSession.mockRejectedValue(new Error("still down"));

    await executeBookOccurrenceCheckout({
      occurrence,
      guest,
      heldBookingId: 7,
      checkoutKeyByBooking: keys,
      createKeyByIntent: new Map(),
      origin: "http://localhost",
      redirectTo,
    });

    expect(createBooking).toHaveBeenCalledOnce();
    expect(createCheckoutSession).toHaveBeenNthCalledWith(
      2,
      expect.anything(),
      { idempotencyKey: "idem-key-1" },
    );
  });
});
