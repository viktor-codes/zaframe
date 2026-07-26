import { describe, expect, it } from "vitest";
import {
  bookingNeedsCheckoutPayment,
  canCompleteBookingPayment,
  canCustomerCancelBooking,
  getBookingReservationRemainingMs,
  isBookingPaymentSucceeded,
  isPendingBooking,
} from "./booking";

describe("booking model", () => {
  it("detects pending bookings", () => {
    expect(isPendingBooking({ status: "pending" })).toBe(true);
    expect(isPendingBooking({ status: "confirmed" })).toBe(false);
  });

  it("treats payment_status succeeded as paid (not order paid)", () => {
    expect(
      isBookingPaymentSucceeded({ payment_status: "succeeded" }),
    ).toBe(true);
    expect(isBookingPaymentSucceeded({ payment_status: "paid" })).toBe(false);
  });

  it("requires checkout only for pending paid sessions", () => {
    expect(
      bookingNeedsCheckoutPayment(
        { status: "pending", payment_status: "pending" },
        { price_cents: 2500 },
      ),
    ).toBe(true);
    expect(
      bookingNeedsCheckoutPayment(
        { status: "confirmed", payment_status: "succeeded" },
        { price_cents: 2500 },
      ),
    ).toBe(false);
    expect(
      bookingNeedsCheckoutPayment(
        { status: "pending", payment_status: null },
        { price_cents: 0 },
      ),
    ).toBe(false);
  });

  it("blocks Stripe checkout after the pending hold expires", () => {
    const now = new Date("2026-07-06T10:00:00.000Z");
    expect(
      canCompleteBookingPayment(
        {
          status: "pending",
          payment_status: "pending",
          reserved_until: "2026-07-06T09:59:00.000Z",
        },
        { price_cents: 2500 },
        now,
      ),
    ).toBe(false);
    expect(
      canCompleteBookingPayment(
        {
          status: "pending",
          payment_status: "pending",
          reserved_until: "2026-07-06T10:15:00.000Z",
        },
        { price_cents: 2500 },
        now,
      ),
    ).toBe(true);
  });

  it("returns remaining reservation time for pending bookings", () => {
    const now = new Date("2026-07-06T10:00:00.000Z");
    const reservedUntil = "2026-07-06T10:15:00.000Z";

    expect(
      getBookingReservationRemainingMs(
        { status: "pending", reserved_until: reservedUntil },
        now,
      ),
    ).toBe(15 * 60 * 1000);
  });

  it("allows customer cancellation before studio cutoff", () => {
    const now = new Date("2026-07-06T10:00:00.000Z");

    expect(
      canCustomerCancelBooking(
        { status: "confirmed", cancelled_at: null },
        { start_time: "2026-07-07T10:00:00.000Z" },
        { cancel_before_hours: 24 },
        now,
      ),
    ).toBe(true);
  });

  it("blocks customer cancellation inside studio cutoff", () => {
    const now = new Date("2026-07-06T22:00:00.000Z");

    expect(
      canCustomerCancelBooking(
        { status: "confirmed", cancelled_at: null },
        { start_time: "2026-07-07T10:00:00.000Z" },
        { cancel_before_hours: 24 },
        now,
      ),
    ).toBe(false);
  });
});
