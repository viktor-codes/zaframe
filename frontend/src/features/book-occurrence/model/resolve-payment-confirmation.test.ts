import { describe, expect, it } from "vitest";

import {
  resolvePaymentConfirmation,
  shouldContinuePaymentConfirmationPoll,
} from "./resolve-payment-confirmation";

describe("resolvePaymentConfirmation", () => {
  it("stays processing while the booking is still pending", () => {
    expect(
      resolvePaymentConfirmation({
        status: "pending",
        payment_status: "pending",
      }),
    ).toEqual({ phase: "processing" });
  });

  it("confirms when booking status is confirmed", () => {
    expect(
      resolvePaymentConfirmation({
        status: "confirmed",
        payment_status: "succeeded",
      }),
    ).toEqual({ phase: "confirmed" });
  });

  it("keeps polling when payment succeeded but booking is still pending", () => {
    expect(
      resolvePaymentConfirmation({
        status: "pending",
        payment_status: "succeeded",
      }),
    ).toEqual({ phase: "processing" });
  });

  it("surfaces manual review for overbooked webhook outcome", () => {
    expect(
      resolvePaymentConfirmation({
        status: "cancelled",
        payment_status: "overbooked_manual_review",
      }),
    ).toEqual({ phase: "manual_review" });
  });

  it("fails for expired holds", () => {
    expect(
      resolvePaymentConfirmation({
        status: "expired",
        payment_status: null,
      }),
    ).toEqual({ phase: "failed", reason: "expired" });
  });

  it("fails for cancelled bookings without manual-review payment", () => {
    expect(
      resolvePaymentConfirmation({
        status: "cancelled",
        payment_status: null,
      }),
    ).toEqual({ phase: "failed", reason: "cancelled" });
  });

  it("fails when payment_status is failed", () => {
    expect(
      resolvePaymentConfirmation({
        status: "pending",
        payment_status: "failed",
      }),
    ).toEqual({ phase: "failed", reason: "failed_payment" });
  });
});

describe("shouldContinuePaymentConfirmationPoll", () => {
  it("continues only while processing (delayed webhook)", () => {
    expect(shouldContinuePaymentConfirmationPoll({ phase: "processing" })).toBe(
      true,
    );
    expect(shouldContinuePaymentConfirmationPoll({ phase: "confirmed" })).toBe(
      false,
    );
    expect(
      shouldContinuePaymentConfirmationPoll({ phase: "manual_review" }),
    ).toBe(false);
  });
});
