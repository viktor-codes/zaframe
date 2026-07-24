import { describe, expect, it, vi, afterEach } from "vitest";

import { ApiError } from "./api-error";
import { REQUEST_ID_HEADER } from "./request-headers";

vi.mock("@shared/lib/config", () => ({
  config: {
    apiUrl: "https://api.example.com",
    hasBackend: true,
  },
}));

import { fetchStudioPublicBySlug, serverGet } from "./server";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.clearAllMocks();
});

describe("serverGet", () => {
  it("sends X-Request-ID and returns JSON", async function () {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const data = await serverGet<{ ok: boolean }>("api/v1/health", {
      requestId: "req-test-1",
    });

    expect(data).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("https://api.example.com/api/v1/health");
    expect(new Headers(init.headers).get(REQUEST_ID_HEADER)).toBe("req-test-1");
    expect(init.method).toBe("GET");
  });

  it("throws ApiError with requestId from the response header", async function () {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ detail: "Not found", title: "Not Found" }), {
        status: 404,
        headers: {
          "Content-Type": "application/json",
          [REQUEST_ID_HEADER]: "resp-404",
        },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(serverGet("api/v1/missing")).rejects.toMatchObject({
      name: "ApiError",
      status: 404,
      requestId: "resp-404",
      message: "Not found",
    } satisfies Partial<ApiError>);
  });

  it("passes next.revalidate through to fetch", async function () {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([]), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await serverGet("api/v1/studios", {
      next: { revalidate: 60, tags: ["studios"] },
    });

    const init = fetchMock.mock.calls[0][1] as RequestInit & {
      next?: { revalidate?: number; tags?: string[] };
    };
    expect(init.next).toEqual({ revalidate: 60, tags: ["studios"] });
  });
});

describe("fetchStudioPublicBySlug", () => {
  it("calls the public slug endpoint with default revalidate", async function () {
    const payload = { id: 1, name: "Studio", slug: "yoga-lab", services: [] };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchStudioPublicBySlug("yoga-lab");

    expect(result).toEqual(payload);
    const [url, init] = fetchMock.mock.calls[0] as [
      string,
      RequestInit & { next?: { revalidate?: number } },
    ];
    expect(url).toBe(
      "https://api.example.com/api/v1/studios/slug/yoga-lab/public",
    );
    expect(init.next?.revalidate).toBe(60);
  });
});
