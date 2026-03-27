import { describe, expect, it } from "vitest";

import { buildApiUrl } from "./build-url";

describe("buildApiUrl", () => {
  it("joins base and path with leading slash", () => {
    expect(buildApiUrl("https://api.example.com", "/v1/users")).toBe(
      "https://api.example.com/v1/users",
    );
  });

  it("normalizes path without leading slash", () => {
    expect(buildApiUrl("https://api.example.com", "v1/users")).toBe(
      "https://api.example.com/v1/users",
    );
  });

  it("strips trailing slash from base", () => {
    expect(buildApiUrl("https://api.example.com/", "/health")).toBe(
      "https://api.example.com/health",
    );
  });

  it("appends scalar query params", () => {
    expect(
      buildApiUrl("https://api.example.com", "/items", {
        page: 2,
        active: true,
        tag: "yoga",
      }),
    ).toBe("https://api.example.com/items?page=2&active=true&tag=yoga");
  });

  it("repeats keys for array params", () => {
    expect(
      buildApiUrl("https://api.example.com", "/search", {
        category: ["yoga", "pilates"],
      }),
    ).toBe("https://api.example.com/search?category=yoga&category=pilates");
  });

  it("skips undefined params", () => {
    expect(
      buildApiUrl("https://api.example.com", "/x", { a: 1, b: undefined }),
    ).toBe("https://api.example.com/x?a=1");
  });
});
