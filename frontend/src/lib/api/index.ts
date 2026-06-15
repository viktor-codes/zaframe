/**
 * API client and module re-exports.
 */
export {
  api,
  setAuthTokenProvider,
  setRefreshTokensFn,
  ApiError,
} from "./client";
export { getUserFacingApiMessage } from "./error-message";
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
