import { describe, expect, it } from "vitest";

import {
  resolveOrderPaymentConfirmation,
  shouldContinueOrderPaymentConfirmationPoll,
} from "./resolve-order-payment-confirmation";

describe("resolveOrderPaymentConfirmation", () => {
  it("stays processing while the order is pending", () => {
    expect(resolveOrderPaymentConfirmation({ status: "pending" })).toEqual({
      phase: "processing",
    });
  });

  it("confirms when order is paid", () => {
    expect(resolveOrderPaymentConfirmation({ status: "paid" })).toEqual({
      phase: "confirmed",
    });
  });

  it("surfaces manual review", () => {
    expect(
      resolveOrderPaymentConfirmation({ status: "manual_review" }),
    ).toEqual({ phase: "manual_review" });
  });

  it("fails for expired / cancelled / refunded", () => {
    expect(resolveOrderPaymentConfirmation({ status: "expired" })).toEqual({
      phase: "failed",
      reason: "expired",
    });
    expect(resolveOrderPaymentConfirmation({ status: "cancelled" })).toEqual({
      phase: "failed",
      reason: "cancelled",
    });
    expect(resolveOrderPaymentConfirmation({ status: "refunded" })).toEqual({
      phase: "failed",
      reason: "refunded",
    });
  });
});

describe("shouldContinueOrderPaymentConfirmationPoll", () => {
  it("continues only while processing", () => {
    expect(
      shouldContinueOrderPaymentConfirmationPoll({ phase: "processing" }),
    ).toBe(true);
    expect(
      shouldContinueOrderPaymentConfirmationPoll({ phase: "confirmed" }),
    ).toBe(false);
  });
});
