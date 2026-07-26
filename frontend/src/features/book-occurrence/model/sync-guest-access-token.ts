/**
 * Persist `?access_token=` into sessionStorage and strip it from the URL.
 */
export function syncGuestAccessTokenFromQuery(
  bookingId: number,
  accessTokenFromQuery: string | null,
  persist: (bookingId: number, token: string) => void,
): void {
  if (!accessTokenFromQuery) return;
  persist(bookingId, accessTokenFromQuery);

  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  if (!url.searchParams.has("access_token")) return;
  url.searchParams.delete("access_token");
  window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
}

export function parseBookingRouteId(raw: unknown): number | null {
  const id =
    typeof raw === "string" || typeof raw === "number" ? Number(raw) : NaN;
  if (!Number.isInteger(id) || id <= 0) return null;
  return id;
}
