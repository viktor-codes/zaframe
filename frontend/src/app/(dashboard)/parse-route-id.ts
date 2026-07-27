/**
 * Parse a positive integer id from a Next.js `useParams()` segment.
 * Handles `string | string[] | undefined` from the App Router.
 */

import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

export function parsePositiveRouteId(
  value: string | string[] | undefined,
): number | null {
  const raw = Array.isArray(value) ? value[0] : value;
  return parsePositiveIdString(raw);
}
