/** Utils, config, constants, and cross-cutting client helpers. */
export { config } from "./config";
export { cn } from "./utils";
export { formatMoneyFromCents } from "./format-money";
export { getSafeNextPath } from "./safe-next-path";
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
export {
  buildStudioDashboardNav,
  filterStudioDashboardNav,
  type StudioDashboardNavId,
  type StudioDashboardNavItem,
} from "./studio-dashboard-nav";
export { queryKeys } from "./query-keys";
export type {
  StudioOccurrencesParams,
  StudiosListParams,
} from "./query-keys";
export { useNow, type UseNowOptions } from "./use-now";
// WHY: createAppQueryClient stays a deep import (`@shared/lib/query-client`)
// so isomorphic barrels do not pull TanStack Query + module augmentation.
