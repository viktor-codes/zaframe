import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import { setAuthTokenProvider } from "./client";
import { fetchServiceAvailability } from "./services";

describe("fetchServiceAvailability", () => {
  afterEach(() => {
    setAuthTokenProvider(() => null);
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("GETs public availability without session Bearer", async () => {
    setAuthTokenProvider(() => "session-token");
    const payload = {
      service_id: 55,
      can_book: true,
      requires_warning: true,
      warning_message: "Some dates are almost full",
      schedule_details: [
        { date: "2026-08-01", is_overbooked: false, remaining: 2 },
      ],
    };
    const fetchMock = vi.fn(async (input: string | URL) => {
      expect(String(input)).toContain("/api/v1/services/55/availability");
      expect(String(input)).toContain("start_date=2026-08-01");
      return new Response(JSON.stringify(payload), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchServiceAvailability(55, {
      start_date: "2026-08-01",
    });

    const headers = new Headers(fetchMock.mock.calls[0]?.[1]?.headers);
    expect(headers.get("Authorization")).toBeNull();
    expect(result.requires_warning).toBe(true);
    expect(result.schedule_details).toHaveLength(1);
  });

  it("omits start_date when not provided", async () => {
    const fetchMock = vi.fn(async (input: string | URL) => {
      expect(String(input)).not.toContain("start_date=");
      return new Response(
        JSON.stringify({
          service_id: 1,
          can_book: true,
          requires_warning: false,
          warning_message: null,
          schedule_details: [],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchServiceAvailability(1);
    expect(fetchMock).toHaveBeenCalledOnce();
  });
});
