import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import {
  checkInBooking,
  createCourseBooking,
  markBookingNoShow,
} from "./bookings";
import { setAuthTokenProvider } from "./client";

describe("createCourseBooking", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("posts CourseBookingCreate to /bookings and returns order response", async () => {
    const payload = {
      order: {
        id: 9,
        total_amount_cents: 12000,
        currency: "eur",
        status: "pending",
      },
      bookings: [{ id: 1 }, { id: 2 }],
      access_token: "order-access-jwt",
    };
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      expect(String(input)).toContain("/api/v1/bookings");
      expect(init?.method).toBe("POST");
      return new Response(JSON.stringify(payload), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await createCourseBooking(
      {
        service_id: 55,
        guest_name: "Ada",
        guest_email: "ada@example.com",
        guest_phone: "+10000000000",
      },
      { idempotencyKey: "create-course-idem-1" },
    );

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
    expect(headers.get("Idempotency-Key")).toBe("create-course-idem-1");
    const body = JSON.parse(String(fetchMock.mock.calls[0]?.[1]?.body));
    expect(body).toEqual({
      service_id: 55,
      guest_name: "Ada",
      guest_email: "ada@example.com",
      guest_phone: "+10000000000",
    });
    expect(result.access_token).toBe("order-access-jwt");
    expect(result.order.id).toBe(9);
  });
});

describe("attendance mutations", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "session-token");
  });

  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("patches check-in with Bearer", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      expect(String(input)).toContain("/api/v1/bookings/42/check-in");
      expect(init?.method).toBe("PATCH");
      return new Response(
        JSON.stringify({
          id: 42,
          occurrence_id: 7,
          user_id: null,
          status: "completed",
          created_at: "2026-07-27T10:00:00Z",
          updated_at: "2026-07-27T10:05:00Z",
          cancelled_at: null,
          checked_in_at: "2026-07-27T10:05:00Z",
          is_guest_booking: true,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await checkInBooking(42);
    expect(result.checked_in_at).toBeTruthy();
    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBe("Bearer session-token");
  });

  it("patches mark-no-show with Bearer", async () => {
    const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
      expect(String(input)).toContain("/api/v1/bookings/42/mark-no-show");
      expect(init?.method).toBe("PATCH");
      return new Response(
        JSON.stringify({
          id: 42,
          occurrence_id: 7,
          user_id: null,
          status: "no_show",
          created_at: "2026-07-27T10:00:00Z",
          updated_at: "2026-07-27T10:05:00Z",
          cancelled_at: null,
          no_show_at: "2026-07-27T10:05:00Z",
          is_guest_booking: true,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await markBookingNoShow(42);
    expect(result.status).toBe("no_show");
  });
});
