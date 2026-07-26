/**
 * Persist guest booking access_token from a deep link and scrub it from the URL.
 *
 * Canonical deep link: `/bookings/{id}/confirm#access_token=…` (hash is not sent
 * to servers/CDN logs). Query `?access_token=` is still accepted once for
 * backward compatibility, then stripped.
 */

export function parseBookingRouteId(raw: unknown): number | null {
  const id =
    typeof raw === "string" || typeof raw === "number" ? Number(raw) : NaN;
  if (!Number.isInteger(id) || id <= 0) return null;
  return id;
}

/** Read access_token from a URL hash fragment (`#access_token=…`). */
export function readAccessTokenFromHash(hash: string): string | null {
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  if (!raw) return null;
  const params = new URLSearchParams(raw);
  const token = params.get("access_token")?.trim();
  return token || null;
}

/** Read access_token from hash (preferred) or query (legacy). */
export function readGuestAccessTokenFromLocation(
  href: string,
  hash: string,
): string | null {
  const fromHash = readAccessTokenFromHash(hash);
  if (fromHash) return fromHash;
  try {
    const fromQuery = new URL(href).searchParams.get("access_token")?.trim();
    return fromQuery || null;
  } catch {
    return null;
  }
}

function scrubAccessTokenFromLocation(): void {
  if (typeof window === "undefined") return;
  const url = new URL(window.location.href);
  const hadQuery = url.searchParams.has("access_token");
  if (hadQuery) {
    url.searchParams.delete("access_token");
  }

  const hashParams = new URLSearchParams(
    url.hash.startsWith("#") ? url.hash.slice(1) : url.hash,
  );
  const hadHash = hashParams.has("access_token");
  if (hadHash) {
    hashParams.delete("access_token");
  }

  if (!hadQuery && !hadHash) return;

  const nextHash = hashParams.toString();
  url.hash = nextHash ? `#${nextHash}` : "";
  window.history.replaceState(
    {},
    "",
    `${url.pathname}${url.search}${url.hash}`,
  );
}

/**
 * Persist token from hash/query into sessionStorage and strip it from the URL.
 * Returns the token that was persisted, or null when none was present.
 */
export function syncGuestAccessTokenFromLocation(
  bookingId: number,
  persist: (bookingId: number, token: string) => void,
): string | null {
  if (typeof window === "undefined") return null;

  const token = readGuestAccessTokenFromLocation(
    window.location.href,
    window.location.hash,
  );
  if (!token) return null;

  persist(bookingId, token);
  scrubAccessTokenFromLocation();
  return token;
}

/**
 * @deprecated Prefer {@link syncGuestAccessTokenFromLocation}. Kept for tests
 * that pass an explicit query token.
 */
export function syncGuestAccessTokenFromQuery(
  bookingId: number,
  accessTokenFromQuery: string | null,
  persist: (bookingId: number, token: string) => void,
): void {
  if (!accessTokenFromQuery?.trim()) {
    syncGuestAccessTokenFromLocation(bookingId, persist);
    return;
  }
  persist(bookingId, accessTokenFromQuery.trim());
  scrubAccessTokenFromLocation();
}
