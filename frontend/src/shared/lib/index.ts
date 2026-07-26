/** Utils, config, constants, and cross-cutting client helpers. */
export { config } from "./config";
export { cn } from "./utils";
export { useUIStore, type HeaderVariant } from "./ui-store";
export {
  getGuestBookingAccessToken,
  getGuestBookingSnapshot,
  persistGuestBookingAccessToken,
  storeGuestBookingAccess,
  updateGuestBookingSnapshot,
  type GuestBookingSnapshot,
} from "./booking-guest-token";
export * from "./constants";
export { queryKeys } from "./query-keys";
export type {
  StudioOccurrencesParams,
  StudiosListParams,
} from "./query-keys";
// WHY: createAppQueryClient stays a deep import (`@shared/lib/query-client`)
// so isomorphic barrels do not pull TanStack Query + module augmentation.
