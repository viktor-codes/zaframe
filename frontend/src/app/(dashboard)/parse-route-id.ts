/**
 * Parse a positive numeric id from a Next.js `useParams()` segment.
 * Handles `string | string[] | undefined` from the App Router.
 */
export function parsePositiveRouteId(
  value: string | string[] | undefined,
): number | null {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw == null || raw === "") {
    return null;
  }

  const id = Number(raw);
  return Number.isFinite(id) && id > 0 ? id : null;
}
