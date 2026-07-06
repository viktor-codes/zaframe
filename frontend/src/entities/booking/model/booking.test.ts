import { describe, expect, it } from "vitest";
import {
  canCustomerCancelBooking,
  getBookingReservationRemainingMs,
  isPendingBooking,
} from "./booking";

describe("booking model", () => {
  it("detects pending bookings", () => {
    expect(isPendingBooking({ status: "pending" })).toBe(true);
    expect(isPendingBooking({ status: "confirmed" })).toBe(false);
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
