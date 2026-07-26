import { describe, expect, it } from "vitest";
import {
  getCancelDeadline,
  getCancelPolicyHint,
} from "./booking-cancel-policy";

describe("getCancelDeadline", () => {
  it("subtracts cancel_before_hours from session start", () => {
    const deadline = getCancelDeadline("2026-07-10T18:00:00.000Z", 24);
    expect(deadline.toISOString()).toBe("2026-07-09T18:00:00.000Z");
  });
});

describe("getCancelPolicyHint", () => {
  const occurrence = { start_time: "2026-07-10T18:00:00.000Z" };
  const studio = { cancel_before_hours: 24 };

  it("returns allowed hint before cutoff", () => {
    const hint = getCancelPolicyHint(
      { status: "confirmed", cancelled_at: null },
      occurrence,
      studio,
      new Date("2026-07-08T12:00:00.000Z"),
    );
    expect(hint?.kind).toBe("allowed");
    if (hint?.kind === "allowed") {
      expect(hint.deadlineLabel.length).toBeGreaterThan(0);
    }
  });

  it("returns closed hint after cutoff", () => {
    expect(
      getCancelPolicyHint(
        { status: "confirmed", cancelled_at: null },
        occurrence,
        studio,
        new Date("2026-07-10T10:00:00.000Z"),
      ),
    ).toEqual({ kind: "closed", cancelBeforeHours: 24 });
  });

  it("returns null for cancelled bookings", () => {
    expect(
      getCancelPolicyHint(
        {
          status: "cancelled",
          cancelled_at: "2026-07-07T10:00:00.000Z",
        },
        occurrence,
        studio,
      ),
    ).toBeNull();
  });

  it("returns null for expired unpaid holds", () => {
    expect(
      getCancelPolicyHint(
        {
          status: "pending",
          cancelled_at: null,
          reserved_until: "2026-07-08T11:00:00.000Z",
        },
        occurrence,
        studio,
        new Date("2026-07-08T12:00:00.000Z"),
      ),
    ).toBeNull();
  });
});
