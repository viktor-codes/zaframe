/**
 * Extract studio id from dashboard routes like `/dashboard/studios/12/bookings`.
 * Returns null for `/dashboard`, `/dashboard/studios/new`, and non-numeric segments.
 */
export function parseDashboardStudioId(pathname: string): number | null {
  const match = pathname.match(/^\/dashboard\/studios\/(\d+)(?:\/|$)/);
  if (!match) {
    return null;
  }

  const studioId = Number(match[1]);
  return Number.isFinite(studioId) && studioId > 0 ? studioId : null;
}
