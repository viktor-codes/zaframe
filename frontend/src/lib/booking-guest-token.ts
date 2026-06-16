/**
 * Guest checkout token from POST /bookings (one-time, not returned on GET).
 * Stored in sessionStorage for the confirm page and Stripe checkout.
 */

const TOKEN_PREFIX = "zaframe_booking_access_token_";
const SNAPSHOT_PREFIX = "zaframe_booking_snapshot_";

export interface GuestBookingSnapshot {
  id: number;
  occurrence_id: number;
  guest_name: string | null;
  guest_email: string | null;
  status: string;
  payment_status: string | null;
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
