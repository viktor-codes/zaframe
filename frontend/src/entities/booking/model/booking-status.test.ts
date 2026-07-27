import { describe, expect, it } from "vitest";
import { getBookingStatusPresentation } from "./booking-status";

describe("getBookingStatusPresentation", () => {
  it("maps confirmed and cancelled statuses", () => {
    expect(getBookingStatusPresentation({ status: "confirmed" })).toEqual({
      label: "Confirmed",
      tone: "green",
    });
    expect(getBookingStatusPresentation({ status: "cancelled" })).toEqual({
      label: "Cancelled",
      tone: "neutral",
    });
  });

  it("labels pending unpaid holds as pending payment", () => {
    expect(
      getBookingStatusPresentation(
        {
          status: "pending",
          payment_status: "pending",
          reserved_until: "2026-07-06T12:00:00.000Z",
        },
        new Date("2026-07-06T10:00:00.000Z"),
      ),
    ).toEqual({ label: "Pending payment", tone: "amber" });
  });

  it("labels expired reservation holds", () => {
    expect(
      getBookingStatusPresentation(
        {
          status: "pending",
          payment_status: "pending",
          reserved_until: "2026-07-06T09:00:00.000Z",
        },
        new Date("2026-07-06T10:00:00.000Z"),
      ),
    ).toEqual({ label: "Hold expired", tone: "red" });
  });

  it("maps expired booking status", () => {
    expect(getBookingStatusPresentation({ status: "expired" })).toEqual({
      label: "Expired",
      tone: "red",
    });
  });

  it("labels studio-cancelled sessions distinctly", () => {
    expect(
      getBookingStatusPresentation({
        status: "cancelled",
        occurrenceStatus: "cancelled",
      }),
    ).toEqual({ label: "Cancelled by studio", tone: "red" });
  });
});
