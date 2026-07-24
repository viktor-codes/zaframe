import { describe, expect, it } from "vitest";

import { ApiError } from "./api-error";
import { throwApiError } from "./http-error";
import { REQUEST_ID_HEADER } from "./request-headers";

describe("throwApiError", () => {
  it("prefers response header request id", () => {
    const response = new Response(null, {
      status: 400,
      statusText: "Bad Request",
      headers: { [REQUEST_ID_HEADER]: "from-header" },
    });

    expect(() =>
      throwApiError(response, { detail: "Nope" }, "outbound"),
    ).toThrow(ApiError);

    try {
      throwApiError(response, { detail: "Nope" }, "outbound");
    } catch (error) {
      expect(error).toMatchObject({
        message: "Nope",
        status: 400,
        requestId: "from-header",
      });
    }
  });

  it("falls back to outbound request id", () => {
    const response = new Response(null, {
      status: 503,
      statusText: "Unavailable",
    });

    try {
      throwApiError(response, undefined, "outbound-fallback");
    } catch (error) {
      expect(error).toMatchObject({
        requestId: "outbound-fallback",
        status: 503,
      });
    }
  });
});
