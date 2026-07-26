import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import { cancelBooking, fetchBooking } from "./bookings";
import {
  api,
  REQUEST_ID_HEADER,
  setAuthTokenProvider,
  setRefreshTokensFn,
} from "./client";

interface RecordedCall {
  url: string;
  authorization: string | null;
  requestId: string | null;
}

interface FetchStub {
  calls: RecordedCall[];
  refreshCalls: number;
}

/**
 * Stub fetch with a per-path status queue; unlisted paths answer 200.
 * Repeated calls to one path walk down its queue, so `[401, 200]` models
 * "access token expired, retry after refresh succeeded".
 */
function stubFetch(statusesByPath: Record<string, number[]> = {}): FetchStub {
  const stub: FetchStub = { calls: [], refreshCalls: 0 };
  const cursors = new Map<string, number>();

  const fetchMock = vi.fn(async (input: string | URL, init?: RequestInit) => {
    const url = String(input);
    const headers = new Headers(init?.headers);
    stub.calls.push({
      url,
      authorization: headers.get("Authorization"),
      requestId: headers.get(REQUEST_ID_HEADER),
    });
    if (url.includes("/auth/refresh")) {
      stub.refreshCalls += 1;
    }

    const path = Object.keys(statusesByPath).find((key) => url.includes(key));
    let status = 200;
    if (path) {
      const queue = statusesByPath[path];
      const index = cursors.get(path) ?? 0;
      status = queue[Math.min(index, queue.length - 1)];
      cursors.set(path, index + 1);
    }

    return new Response(JSON.stringify({ ok: true }), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  });

  vi.stubGlobal("fetch", fetchMock);
  return stub;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("api client token refresh", () => {
  beforeEach(() => {
    setAuthTokenProvider(() => "expired-token");
  });

  it("refreshes once when several requests get 401 in parallel", async () => {
    let refreshInvocations = 0;
    setRefreshTokensFn(async () => {
      refreshInvocations += 1;
      await new Promise((resolve) => setTimeout(resolve, 5));
      return { access_token: "fresh-token" };
    });
    const stub = stubFetch({
      "/first": [401, 200],
      "/second": [401, 200],
      "/third": [401, 200],
    });

    await Promise.all([
      api.get("api/v1/first"),
      api.get("api/v1/second"),
      api.get("api/v1/third"),
    ]);

    // WHY: the API revokes every session when a rotated refresh token is replayed.
    expect(refreshInvocations).toBe(1);
    expect(
      stub.calls.filter((call) => call.authorization === "Bearer fresh-token"),
    ).toHaveLength(3);
  });

  it("does not refresh again when the refresh call itself returns 401", async () => {
    setRefreshTokensFn(async () => {
      await api.post("/api/v1/auth/refresh", undefined, {
        skipAuth: true,
        skipRefresh: true,
      });
      return { access_token: "unreachable" };
    });
    const stub = stubFetch({ "/auth/me": [401], "/auth/refresh": [401] });

    await expect(api.get("api/v1/auth/me")).rejects.toThrow();
    expect(stub.refreshCalls).toBe(1);
  });

  it("surfaces 401 without refreshing when the caller skipped auth", async () => {
    const refreshTokens = vi.fn(async () => ({ access_token: "fresh-token" }));
    setRefreshTokensFn(refreshTokens);
    stubFetch({ "/public": [401] });

    await expect(api.get("api/v1/public", { skipAuth: true })).rejects.toThrow();
    expect(refreshTokens).not.toHaveBeenCalled();
  });

  it("keeps the same X-Request-ID on the retried request", async () => {
    setRefreshTokensFn(async () => ({ access_token: "fresh-token" }));
    const stub = stubFetch({ "/protected": [401, 200] });

    await api.get("api/v1/protected");

    expect(stub.calls).toHaveLength(2);
    expect(stub.calls[0].requestId).toBeTruthy();
    expect(stub.calls[1].requestId).toBe(stub.calls[0].requestId);
  });

  it("propagates the original 401 when refresh yields no token", async () => {
    setRefreshTokensFn(async () => null);
    const stub = stubFetch({ "/protected": [401] });

    await expect(api.get("api/v1/protected")).rejects.toMatchObject({
      status: 401,
    });
    expect(stub.calls).toHaveLength(1);
  });

  it("refreshes again for a later burst once the first one settled", async () => {
    let refreshInvocations = 0;
    setRefreshTokensFn(async () => {
      refreshInvocations += 1;
      return { access_token: `fresh-${refreshInvocations}` };
    });
    stubFetch({ "/protected": [401, 200, 401, 200] });

    await api.get("api/v1/protected");
    await api.get("api/v1/protected");

    expect(refreshInvocations).toBe(2);
  });
});

describe("bookings api authentication", () => {
  it("sends Authorization on booking read and cancel", async () => {
    setAuthTokenProvider(() => "user-token");
    setRefreshTokensFn(async () => null);
    const stub = stubFetch();

    await fetchBooking(7);
    await cancelBooking(7);

    expect(stub.calls).toHaveLength(2);
    expect(stub.calls.map((call) => call.authorization)).toEqual([
      "Bearer user-token",
      "Bearer user-token",
    ]);
  });
});
