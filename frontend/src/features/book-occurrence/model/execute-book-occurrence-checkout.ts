/**
 * Pure-ish checkout orchestration (create once → Stripe or free confirm).
 * Kept out of the React hook so the hook stays thin and retry rules are explicit.
 */

import {
  createBooking,
  createCheckoutSession,
  createIdempotencyKey,
  getUserFacingApiMessage,
} from "@shared/api";
import {
  getGuestBookingAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestBookingAccess,
} from "@shared/lib";
import type { OccurrenceResponse } from "@entities/occurrence";

import type { GuestDetails } from "./guest-details-schema";

export type BookOccurrenceCheckoutResult =
  | { kind: "stripe"; bookingId: number }
  | { kind: "free"; bookingId: number }
  | { kind: "checkout_failed"; bookingId: number; message: string };

export interface ExecuteBookOccurrenceCheckoutInput {
  occurrence: OccurrenceResponse;
  guest: GuestDetails;
  /** When set, skip createBooking and retry checkout for this hold. */
  heldBookingId: number | null;
  checkoutKeyByBooking: Map<number, string>;
  origin: string;
  /** Navigate to Stripe Checkout (injected to keep this module window-free). */
  redirectTo: (url: string) => void;
}

const CHECKOUT_FAILED_FALLBACK =
  "Payment could not be started. Your seat is held — open booking details to retry.";

function checkoutIdempotencyKeyFor(
  keys: Map<number, string>,
  bookingId: number,
): string {
  const existing = keys.get(bookingId);
  if (existing) return existing;
  const key = createIdempotencyKey();
  keys.set(bookingId, key);
  return key;
}

export async function executeBookOccurrenceCheckout({
  occurrence,
  guest,
  heldBookingId,
  checkoutKeyByBooking,
  origin,
  redirectTo,
}: ExecuteBookOccurrenceCheckoutInput): Promise<BookOccurrenceCheckoutResult> {
  let bookingId = heldBookingId;
  let accessToken: string | null =
    bookingId != null ? getGuestBookingAccessToken(bookingId) : null;

  // WHY: after checkout_failed the seat is already held — retry payment only.
  if (bookingId == null) {
    const booking = await createBooking({
      occurrence_id: occurrence.id,
      guest_name: guest.guest_name,
      guest_email: guest.guest_email,
      guest_phone: guest.guest_phone,
      booking_type: "single",
      service_id: occurrence.service_id,
    });

    bookingId = booking.id;
    accessToken = booking.access_token;
    storeGuestBookingAccess(booking.id, booking.access_token, {
      id: booking.id,
      occurrence_id: booking.occurrence_id,
      guest_name: booking.guest_name ?? null,
      guest_email: booking.guest_email ?? null,
      status: booking.status,
      payment_status: booking.payment_status ?? null,
      reserved_until: booking.reserved_until ?? null,
    });
  }

  // WHY: free sessions have no Stripe Checkout — confirm page is the success UI.
  if (occurrence.price_cents === 0) {
    return { kind: "free", bookingId };
  }

  try {
    const session = await createCheckoutSession(
      {
        booking_id: bookingId,
        success_url: `${origin}/bookings/success?booking=${bookingId}`,
        cancel_url: `${origin}/bookings/cancel?booking=${bookingId}`,
        ...(accessToken ? { access_token: accessToken } : {}),
      },
      {
        idempotencyKey: checkoutIdempotencyKeyFor(
          checkoutKeyByBooking,
          bookingId,
        ),
      },
    );

    const checkoutUrl = getSafeStripeCheckoutUrl(session.checkout_url);
    if (checkoutUrl) {
      redirectTo(checkoutUrl);
      return { kind: "stripe", bookingId };
    }

    return {
      kind: "checkout_failed",
      bookingId,
      message: CHECKOUT_FAILED_FALLBACK,
    };
  } catch (err) {
    return {
      kind: "checkout_failed",
      bookingId,
      message: getUserFacingApiMessage(err) || CHECKOUT_FAILED_FALLBACK,
    };
  }
}
