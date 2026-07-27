import { describe, expect, it } from "vitest";
import { getOrderStatusPresentation } from "./order-status";

describe("getOrderStatusPresentation", () => {
  it("maps paid and pending statuses", () => {
    expect(getOrderStatusPresentation("paid")).toEqual({
      label: "Paid",
      tone: "green",
    });
    expect(getOrderStatusPresentation("pending")).toEqual({
      label: "Pending payment",
      tone: "amber",
    });
  });

  it("includes detail for manual_review and expired", () => {
    expect(getOrderStatusPresentation("manual_review").detail).toMatch(
      /verified/i,
    );
    expect(getOrderStatusPresentation("expired").detail).toMatch(/expired/i);
  });
});
