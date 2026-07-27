/**
 * Parse a strict positive integer from a query/route string.
 *
 * WHY: `Number("1.5")` / `Number("1e2")` are finite and would produce bad
 * hrefs or API calls if used raw from `searchParams` / path segments.
 */
export function parsePositiveIdString(
  raw: string | null | undefined,
): number | null {
  if (raw == null) return null;
  const trimmed = raw.trim();
  if (trimmed === "" || !/^\d+$/.test(trimmed)) return null;
  const id = Number(trimmed);
  return Number.isInteger(id) && id > 0 ? id : null;
}
