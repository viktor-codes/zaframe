/**
 * Course checkout orchestration (create order once → Stripe or free success).
 */

import {
  createCourseBooking,
  createIdempotencyKey,
  createOrderCheckoutSession,
  getUserFacingApiMessage,
} from "@shared/api";
import {
  getGuestOrderAccessToken,
  getSafeStripeCheckoutUrl,
  storeGuestOrderAccess,
} from "@shared/lib";

import type { GuestDetails } from "./guest-details-schema";

export type BookCourseCheckoutResult =
  | { kind: "stripe"; orderId: number; totalAmountCents: number }
  | { kind: "free"; orderId: number; totalAmountCents: number }
  | {
      kind: "checkout_failed";
      orderId: number;
      totalAmountCents: number;
      message: string;
    };

export interface ExecuteBookCourseCheckoutInput {
  serviceId: number;
  guest: GuestDetails;
  /** When set, skip createCourseBooking and retry checkout for this hold. */
  heldOrderId: number | null;
  /** Known total from create response; used on retry when create is skipped. */
  heldTotalAmountCents: number | null;
  checkoutKeyByOrder: Map<number, string>;
  origin: string;
  redirectTo: (url: string) => void;
}

const CHECKOUT_FAILED_FALLBACK =
  "Payment could not be started. Your course seats are held — retry payment to continue.";

function checkoutIdempotencyKeyFor(
  keys: Map<number, string>,
  orderId: number,
): string {
  const existing = keys.get(orderId);
  if (existing) return existing;
  const key = createIdempotencyKey();
  keys.set(orderId, key);
  return key;
}

export async function executeBookCourseCheckout({
  serviceId,
  guest,
  heldOrderId,
  heldTotalAmountCents,
  checkoutKeyByOrder,
  origin,
  redirectTo,
}: ExecuteBookCourseCheckoutInput): Promise<BookCourseCheckoutResult> {
  let orderId = heldOrderId;
  let totalAmountCents = heldTotalAmountCents;
  let accessToken: string | null =
    orderId != null ? getGuestOrderAccessToken(orderId) : null;

  // WHY: after checkout_failed the order is already created — retry payment only.
  if (orderId == null) {
    const created = await createCourseBooking({
      service_id: serviceId,
      guest_name: guest.guest_name,
      guest_email: guest.guest_email,
      guest_phone: guest.guest_phone,
    });

    orderId = created.order.id;
    totalAmountCents = created.order.total_amount_cents;
    accessToken = created.access_token;
    storeGuestOrderAccess(created.order.id, created.access_token, {
      id: created.order.id,
      service_id: created.order.service_id,
      guest_name: created.order.guest_name ?? null,
      guest_email: created.order.guest_email ?? null,
      status: created.order.status,
      total_amount_cents: created.order.total_amount_cents,
      currency: created.order.currency,
    });
  }

  // WHY: free courses have no Stripe Checkout — success page is the confirm UI.
  if ((totalAmountCents ?? 0) === 0) {
    return { kind: "free", orderId, totalAmountCents: 0 };
  }

  const amountCents = totalAmountCents ?? 0;

  try {
    const session = await createOrderCheckoutSession(
      {
        order_id: orderId,
        success_url: `${origin}/bookings/success?order=${orderId}`,
        cancel_url: `${origin}/bookings/cancel?order=${orderId}`,
        ...(accessToken ? { access_token: accessToken } : {}),
      },
      {
        idempotencyKey: checkoutIdempotencyKeyFor(checkoutKeyByOrder, orderId),
      },
    );

    const checkoutUrl = getSafeStripeCheckoutUrl(session.checkout_url);
    if (checkoutUrl) {
      redirectTo(checkoutUrl);
      return { kind: "stripe", orderId, totalAmountCents: amountCents };
    }

    return {
      kind: "checkout_failed",
      orderId,
      totalAmountCents: amountCents,
      message: CHECKOUT_FAILED_FALLBACK,
    };
  } catch (err) {
    return {
      kind: "checkout_failed",
      orderId,
      totalAmountCents: amountCents,
      message: getUserFacingApiMessage(err) || CHECKOUT_FAILED_FALLBACK,
    };
  }
}
