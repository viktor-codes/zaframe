import { describe, expect, it } from "vitest";

import { resolveApiUrls } from "./config";

describe("resolveApiUrls", () => {
  it("uses public URL for the browser and upstream when both are set", () => {
    expect(
      resolveApiUrls({
        NEXT_PUBLIC_API_URL: "https://app.example.com/",
        API_UPSTREAM_URL: "https://api.example.com/",
      }),
    ).toEqual({
      apiUrl: "https://app.example.com",
      apiUpstreamUrl: "https://api.example.com",
      hasBackend: true,
    });
  });

  it("falls back upstream to the public URL when API_UPSTREAM_URL is missing", () => {
    expect(
      resolveApiUrls({
        NEXT_PUBLIC_API_URL: "http://localhost:3000",
      }),
    ).toEqual({
      apiUrl: "http://localhost:3000",
      apiUpstreamUrl: "http://localhost:3000",
      hasBackend: true,
    });
  });

  it("reports hasBackend false when the public URL is empty", () => {
    expect(
      resolveApiUrls({
        API_UPSTREAM_URL: "http://127.0.0.1:8000",
      }),
    ).toEqual({
      apiUrl: "",
      apiUpstreamUrl: "http://127.0.0.1:8000",
      hasBackend: false,
    });
  });
});
