import { describe, expect, it } from "vitest";
import {
  compareBookingsForBucket,
  getBookingListBucket,
} from "./booking-list-bucket";

describe("getBookingListBucket", () => {
  const now = new Date("2026-07-10T12:00:00.000Z");

  it("puts cancelled bookings in cancelled regardless of session time", () => {
    expect(
      getBookingListBucket(
        {
          status: "cancelled",
          cancelled_at: "2026-07-09T10:00:00.000Z",
          occurrence: { start_time: "2026-07-20T18:00:00.000Z" },
        },
        now,
      ),
    ).toBe("cancelled");
  });

  it("splits active bookings by session start", () => {
    expect(
      getBookingListBucket(
        {
          status: "confirmed",
          cancelled_at: null,
          occurrence: { start_time: "2026-07-10T12:00:00.000Z" },
        },
        now,
      ),
    ).toBe("upcoming");
    expect(
      getBookingListBucket(
        {
          status: "confirmed",
          cancelled_at: null,
          occurrence: { start_time: "2026-07-10T11:59:00.000Z" },
        },
        now,
      ),
    ).toBe("past");
  });
});

describe("compareBookingsForBucket", () => {
  it("sorts upcoming ascending and past descending by start time", () => {
    const earlier = {
      status: "confirmed",
      cancelled_at: null,
      occurrence: { start_time: "2026-07-11T10:00:00.000Z" },
    };
    const later = {
      status: "confirmed",
      cancelled_at: null,
      occurrence: { start_time: "2026-07-12T10:00:00.000Z" },
    };

    expect(compareBookingsForBucket("upcoming", earlier, later)).toBeLessThan(
      0,
    );
    expect(compareBookingsForBucket("past", earlier, later)).toBeGreaterThan(0);
  });
});
