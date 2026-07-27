/**
 * Shared HTTP error helpers (isomorphic — safe for client and server modules).
 */

import { ApiError } from "./api-error";
import { resolveRequestIdFromResponse } from "./request-headers";

export async function safeParseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

/**
 * Build and throw ApiError from a failed response.
 *
 * @param fallbackRequestId - Outbound `X-Request-ID` when the response omits it
 */
export function throwApiError(
  response: Response,
  body: unknown,
  fallbackRequestId?: string,
): never {
  const requestId =
    resolveRequestIdFromResponse(response, body) ?? fallbackRequestId;
  const detail =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail?: unknown }).detail
      : undefined;
  const message =
    typeof detail === "string" && detail.trim()
      ? detail
      : response.statusText || "Request failed";

  throw new ApiError(message, response.status, body, requestId);
}
