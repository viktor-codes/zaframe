/**
 * Guest checkout token from POST /bookings (not returned on later GETs).
 * Stored in sessionStorage for the confirm page and Stripe checkout.
 * May also arrive once via `?access_token=` on `/bookings/{id}/confirm`.
 */

const TOKEN_PREFIX = "zeeframe_booking_access_token_";
const SNAPSHOT_PREFIX = "zeeframe_booking_snapshot_";

export interface GuestBookingSnapshot {
  id: number;
  occurrence_id: number;
  guest_name: string | null;
  guest_email: string | null;
  status: string;
  payment_status: string | null;
  reserved_until?: string | null;
}

export function storeGuestBookingAccess(
  bookingId: number,
  accessToken: string,
  snapshot: GuestBookingSnapshot,
): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(`${TOKEN_PREFIX}${bookingId}`, accessToken);
  sessionStorage.setItem(
    `${SNAPSHOT_PREFIX}${bookingId}`,
    JSON.stringify(snapshot),
  );
}

/** Persist token from email / deep-link query without overwriting an existing snapshot. */
export function persistGuestBookingAccessToken(
  bookingId: number,
  accessToken: string,
): void {
  if (typeof window === "undefined") return;
  const trimmed = accessToken.trim();
  if (!trimmed) return;
  sessionStorage.setItem(`${TOKEN_PREFIX}${bookingId}`, trimmed);
}

export function getGuestBookingAccessToken(bookingId: number): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(`${TOKEN_PREFIX}${bookingId}`);
}

export function getGuestBookingSnapshot(
  bookingId: number,
): GuestBookingSnapshot | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(`${SNAPSHOT_PREFIX}${bookingId}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as GuestBookingSnapshot;
  } catch {
    return null;
  }
}

export function updateGuestBookingSnapshot(
  bookingId: number,
  patch: Partial<GuestBookingSnapshot>,
): void {
  if (typeof window === "undefined") return;
  const current = getGuestBookingSnapshot(bookingId);
  if (!current) return;
  sessionStorage.setItem(
    `${SNAPSHOT_PREFIX}${bookingId}`,
    JSON.stringify({ ...current, ...patch, id: bookingId }),
  );
}
