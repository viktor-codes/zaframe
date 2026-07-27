import { describe, expect, it } from "vitest";
import { getBookingTimelineEvents } from "./booking-timeline";

describe("getBookingTimelineEvents", () => {
  it("always includes booked and session events", () => {
    const events = getBookingTimelineEvents({
      status: "confirmed",
      created_at: "2026-07-01T10:00:00.000Z",
      occurrence: {
        start_time: "2026-07-10T18:00:00.000Z",
        end_time: "2026-07-10T19:00:00.000Z",
        status: "scheduled",
      },
    });

    expect(events.map((event) => event.id)).toEqual(["created", "session"]);
  });

  it("includes studio cancellation with reason detail", () => {
    const events = getBookingTimelineEvents({
      status: "cancelled",
      created_at: "2026-07-01T10:00:00.000Z",
      cancelled_at: "2026-07-05T12:00:00.000Z",
      occurrence: {
        start_time: "2026-07-10T18:00:00.000Z",
        end_time: "2026-07-10T19:00:00.000Z",
        status: "cancelled",
        cancelled_at: "2026-07-05T11:00:00.000Z",
        cancellation_reason: "Instructor ill",
      },
    });

    const studioCancel = events.find(
      (event) => event.id === "occurrence-cancelled",
    );
    expect(studioCancel).toMatchObject({
      label: "Session cancelled by the studio",
      detail: "Instructor ill",
      tone: "danger",
    });
    expect(events.map((event) => event.id)).toEqual([
      "created",
      "occurrence-cancelled",
      "booking-cancelled",
      "session",
    ]);
  });

  it("sorts events chronologically", () => {
    const events = getBookingTimelineEvents({
      status: "confirmed",
      created_at: "2026-07-01T10:00:00.000Z",
      reserved_until: "2026-07-01T10:15:00.000Z",
      checked_in_at: "2026-07-10T18:05:00.000Z",
      occurrence: {
        start_time: "2026-07-10T18:00:00.000Z",
        end_time: "2026-07-10T19:00:00.000Z",
        status: "scheduled",
      },
    });

    expect(events.map((event) => event.id)).toEqual([
      "created",
      "hold",
      "session",
      "checked-in",
    ]);
  });
});
