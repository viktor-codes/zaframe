/**
 * API client and module re-exports.
 *
 * @deprecated Import from `@shared/api` — kept for gradual migration.
 */
export {
  api,
  setAuthTokenProvider,
  setRefreshTokensFn,
  ApiError,
  getUserFacingApiMessage,
} from "@shared/api";
export {
  fetchStudios,
  fetchStudiosCount,
  fetchStudio,
  createStudio,
  updateStudio,
  deleteStudio,
  fetchStudioOccurrences,
} from "./studios";
export {
  fetchOccurrence,
  createOccurrence,
  updateOccurrence,
  deleteOccurrence,
  fetchOccurrenceBookings,
} from "./occurrences";
export {
  fetchBookings,
  fetchMyBookings,
  fetchBookingsCount,
  fetchBooking,
  createBooking,
  cancelBooking,
} from "./bookings";
export { createCheckoutSession } from "./payments";
export { requestMagicLink, verifyMagicLink } from "./auth";
export { fetchSearch } from "./search";
