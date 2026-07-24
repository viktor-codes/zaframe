/**
 * Correlation and idempotency helpers (isomorphic).
 *
 * WHY: backend accepts client `X-Request-ID` (≤128 printable chars) and requires
 * a caller-stable `Idempotency-Key` on payment checkout mutations.
 */

export const REQUEST_ID_HEADER = "X-Request-ID";
export const IDEMPOTENCY_KEY_HEADER = "Idempotency-Key";

/**
 * Returns a new UUID suitable for `X-Request-ID` / `Idempotency-Key`.
 */
export function createRequestId(): string {
  return crypto.randomUUID();
}

/**
 * Generate an idempotency key for a single logical mutation attempt.
 *
 * WHY: callers must keep the same key across retries (timeout / double-submit).
 * Do not generate a fresh key inside API wrappers on every call.
 */
export function createIdempotencyKey(): string {
  return createRequestId();
}

/**
 * Prefer response header, then RFC 7807 `request_id` in the body.
 */
export function resolveRequestIdFromResponse(
  response: Response,
  body: unknown,
): string | undefined {
  const fromHeader = response.headers.get(REQUEST_ID_HEADER)?.trim();
  if (fromHeader) return fromHeader;

  if (body && typeof body === "object" && "request_id" in body) {
    const value = (body as { request_id?: unknown }).request_id;
    if (typeof value === "string" && value.trim()) return value.trim();
  }

  return undefined;
}
