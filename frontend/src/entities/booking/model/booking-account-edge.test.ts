import { describe, expect, it } from "vitest";
import {
  getBookingAccountEdge,
  getStudioRebookHref,
  isSessionCancelledByStudio,
} from "./booking-account-edge";

describe("isSessionCancelledByStudio", () => {
  it("detects cancelled occurrence status", () => {
    expect(isSessionCancelledByStudio({ status: "cancelled" })).toBe(true);
    expect(isSessionCancelledByStudio({ status: "scheduled" })).toBe(false);
  });
});

describe("getStudioRebookHref", () => {
  it("prefers public slug route and falls back to studios browse", () => {
    expect(getStudioRebookHref({ slug: "yoga-hub" })).toBe("/s/yoga-hub");
    expect(getStudioRebookHref({ slug: null })).toBe("/studios");
  });
});

describe("getBookingAccountEdge", () => {
  const now = new Date("2026-07-10T12:00:00.000Z");

  it("returns studio cancel notice with reason", () => {
    expect(
      getBookingAccountEdge(
        {
          status: "cancelled",
          cancelled_at: "2026-07-09T10:00:00.000Z",
          occurrence: {
            status: "cancelled",
            cancellation_reason: "Instructor ill",
          },
          studio: { slug: "yoga-hub" },
        },
        now,
      ),
    ).toEqual({
      kind: "studio_cancelled",
      title: "Session cancelled by the studio",
      reason: "Instructor ill",
    });
  });

  it("returns expired edge with rebook href for expired status", () => {
    expect(
      getBookingAccountEdge(
        {
          status: "expired",
          cancelled_at: null,
          occurrence: { status: "scheduled" },
          studio: { slug: "yoga-hub" },
        },
        now,
      ),
    ).toMatchObject({
      kind: "expired",
      title: "Payment window expired",
      rebookHref: "/s/yoga-hub",
      rebookLabel: "Book again",
    });
  });

  it("treats pending hold expiry as expired edge", () => {
    const edge = getBookingAccountEdge(
      {
        status: "pending",
        cancelled_at: null,
        reserved_until: "2026-07-10T11:00:00.000Z",
        occurrence: { status: "scheduled" },
        studio: { slug: null },
      },
      now,
    );
    expect(edge?.kind).toBe("expired");
    if (edge?.kind === "expired") {
      expect(edge.rebookHref).toBe("/studios");
    }
  });
});
