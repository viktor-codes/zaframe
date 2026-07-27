/**
 * Map course create/checkout failures to JTBD copy.
 */

import { ApiError, getUserFacingApiMessage } from "@shared/api";

const HARD_BLOCK_PATTERNS = [
  /not enough seats/i,
  /hard.?limit/i,
  /cannot be purchased/i,
  /course has no upcoming/i,
];

export const COURSE_HARD_BLOCK_CHECKOUT_MESSAGE =
  "This course can’t be purchased right now — some sessions are full. Pick another class or contact the studio.";

export function isCourseHardBlockCheckoutError(error: unknown): boolean {
  if (error instanceof ApiError) {
    const detail = extractDetail(error.body);
    if (detail && HARD_BLOCK_PATTERNS.some((re) => re.test(detail))) {
      return true;
    }
    if (HARD_BLOCK_PATTERNS.some((re) => re.test(error.message))) {
      return true;
    }
  }
  const message = getUserFacingApiMessage(error);
  return HARD_BLOCK_PATTERNS.some((re) => re.test(message));
}

export function getCourseCheckoutErrorMessage(error: unknown): string {
  if (isCourseHardBlockCheckoutError(error)) {
    return COURSE_HARD_BLOCK_CHECKOUT_MESSAGE;
  }
  return getUserFacingApiMessage(error);
}

function extractDetail(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  return null;
}
