import { describe, expect, it } from "vitest";

import { BookingStatus } from "@shared/lib";

import {
  canCheckIn,
  canMarkNoShow,
  getParticipantDisplayName,
} from "./attendance-action";

const confirmed = {
  status: BookingStatus.CONFIRMED,
  checked_in_at: null as string | null,
  no_show_at: null as string | null,
};

describe("canCheckIn", () => {
  it("allows check-in for confirmed bookings", () => {
    expect(canCheckIn(confirmed)).toBe(true);
  });

  it("blocks pending, cancelled, expired, completed, no-show", () => {
    expect(canCheckIn({ ...confirmed, status: BookingStatus.PENDING })).toBe(
      false,
    );
    expect(canCheckIn({ ...confirmed, status: BookingStatus.CANCELLED })).toBe(
      false,
    );
    expect(canCheckIn({ ...confirmed, status: BookingStatus.EXPIRED })).toBe(
      false,
    );
    expect(
      canCheckIn({
        ...confirmed,
        status: BookingStatus.COMPLETED,
        checked_in_at: "2026-07-27T10:00:00Z",
      }),
    ).toBe(false);
    expect(
      canCheckIn({
        ...confirmed,
        status: BookingStatus.NO_SHOW,
        no_show_at: "2026-07-27T10:00:00Z",
      }),
    ).toBe(false);
  });
});

describe("canMarkNoShow", () => {
  it("is true only for confirmed without check-in", () => {
    expect(canMarkNoShow(confirmed)).toBe(true);
    expect(
      canMarkNoShow({
        ...confirmed,
        checked_in_at: "2026-07-27T10:00:00Z",
      }),
    ).toBe(false);
  });
});

describe("getParticipantDisplayName", () => {
  it("prefers name, then email, then booking id", () => {
    expect(
      getParticipantDisplayName({
        id: 1,
        guest_name: "Ada",
        guest_email: "ada@example.com",
      }),
    ).toBe("Ada");
    expect(
      getParticipantDisplayName({
        id: 2,
        guest_name: null,
        guest_email: "ada@example.com",
      }),
    ).toBe("ada@example.com");
    expect(
      getParticipantDisplayName({
        id: 3,
        guest_name: null,
        guest_email: null,
      }),
    ).toBe("Booking #3");
  });
});
