/**
 * Parse a positive integer id from a Next.js `useParams()` segment.
 * Handles `string | string[] | undefined` from the App Router.
 *
 * WHY: `Number.isFinite` accepts floats (`1.5`) and scientific notation (`1e2`);
 * route ids must be strict positive integers only.
 */
export function parsePositiveRouteId(
  value: string | string[] | undefined,
): number | null {
  const raw = Array.isArray(value) ? value[0] : value;
  if (raw == null || raw === "") {
    return null;
  }

  if (!/^\d+$/.test(raw)) {
    return null;
  }

  const id = Number(raw);
  return Number.isInteger(id) && id > 0 ? id : null;
}
