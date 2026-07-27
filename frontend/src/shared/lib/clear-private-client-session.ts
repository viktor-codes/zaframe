/**
 * Scrub guest tokens and private TanStack Query caches on logout / session loss.
 */

import type { QueryClient } from "@tanstack/react-query";

import { clearAllGuestBookingAccess } from "./booking-guest-token";
import { clearAllGuestOrderAccess } from "./order-guest-token";
import { queryKeys } from "./query-keys";

const PRIVATE_QUERY_KEYS: ReadonlyArray<readonly unknown[]> = [
  queryKeys.auth.all,
  queryKeys.bookings.all,
  ["booking"],
  queryKeys.orders.all,
  ["order"],
  queryKeys.studios.my,
  ["studios", "owner"],
];

/**
 * Clear guest sessionStorage PII and authenticated/private query caches.
 *
 * WHY: access token is memory-only, but guest opaque tokens + booking/order
 * detail queries can retain PII across logout on a shared device.
 */
export function clearPrivateClientSession(queryClient: QueryClient): void {
  clearAllGuestBookingAccess();
  clearAllGuestOrderAccess();
  for (const queryKey of PRIVATE_QUERY_KEYS) {
    queryClient.removeQueries({ queryKey });
  }
}
