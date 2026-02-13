/**
 * Реэкспорт API клиента и модулей.
 */
export { api, setAuthTokenProvider, setRefreshTokensFn, ApiError } from "./client";
export {
  fetchStudios,
  fetchStudiosCount,
  fetchStudio,
  createStudio,
  updateStudio,
  deleteStudio,
  fetchStudioSlots,
} from "./studios";
export {
  fetchSlot,
  createSlot,
  updateSlot,
  deleteSlot,
  fetchSlotBookings,
} from "./slots";
export {
  fetchBookings,
  fetchBookingsCount,
  fetchBooking,
  createBooking,
  cancelBooking,
} from "./bookings";
export { createCheckoutSession } from "./payments";
export { requestMagicLink, verifyMagicLink } from "./auth";
export { fetchSearch } from "./search";
