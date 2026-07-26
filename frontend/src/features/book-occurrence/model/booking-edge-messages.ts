/**
 * Map booking/checkout failures to JTBD copy for Phase 3 edge cases.
 */

import { ApiError, getUserFacingApiMessage } from "@shared/api";

const CAPACITY_FULL_PATTERNS = [
  /no seats available/i,
  /no seats left/i,
  /occurrence is full/i,
  /fully booked/i,
];

export const OCCURRENCE_FULL_MESSAGE =
  "No seats left. Pick another time to continue.";

export function isOccurrenceFullCheckoutError(error: unknown): boolean {
  if (error instanceof ApiError) {
    const detail = extractDetail(error.body);
    if (detail && CAPACITY_FULL_PATTERNS.some((re) => re.test(detail))) {
      return true;
    }
    if (CAPACITY_FULL_PATTERNS.some((re) => re.test(error.message))) {
      return true;
    }
  }
  const message = getUserFacingApiMessage(error);
  return CAPACITY_FULL_PATTERNS.some((re) => re.test(message));
}

export function getBookingCheckoutErrorMessage(error: unknown): string {
  if (isOccurrenceFullCheckoutError(error)) {
    return OCCURRENCE_FULL_MESSAGE;
  }
  return getUserFacingApiMessage(error);
}

function extractDetail(body: unknown): string | null {
  if (!body || typeof body !== "object") return null;
  const detail = (body as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;
  return null;
}
