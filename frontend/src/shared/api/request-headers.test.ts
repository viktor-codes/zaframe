import { describe, expect, it } from "vitest";

import {
  createIdempotencyKey,
  createRequestId,
  REQUEST_ID_HEADER,
  resolveRequestIdFromResponse,
} from "./request-headers";

describe("createRequestId / createIdempotencyKey", () => {
  it("returns UUID-shaped strings", () => {
    const id = createRequestId();
    const key = createIdempotencyKey();
    expect(id).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
    expect(key).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i,
    );
  });
});

describe("resolveRequestIdFromResponse", () => {
  it("prefers the response header", () => {
    const response = new Response(null, {
      headers: { [REQUEST_ID_HEADER]: "from-header" },
    });
    expect(
      resolveRequestIdFromResponse(response, { request_id: "from-body" }),
    ).toBe("from-header");
  });

  it("falls back to Problem JSON request_id", () => {
    const response = new Response(null);
    expect(
      resolveRequestIdFromResponse(response, { request_id: "from-body" }),
    ).toBe("from-body");
  });

  it("returns undefined when neither is present", () => {
    const response = new Response(null);
    expect(resolveRequestIdFromResponse(response, { detail: "x" })).toBe(
      undefined,
    );
  });
});
