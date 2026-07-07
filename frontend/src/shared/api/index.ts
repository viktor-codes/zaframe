/** API client, domain fetchers, error helpers, and generated OpenAPI types. */
export { ApiError } from "./api-error";
export {
  api,
  setAuthTokenProvider,
  setRefreshTokensFn,
  type AuthTokenProvider,
  type RefreshTokensFn,
  type RequestConfig,
} from "./client";
export { buildApiUrl, type QueryParamValue, type QueryParams } from "./build-url";
export { getUserFacingApiMessage } from "./error-message";
export type { Schema } from "./schema";
export type { components, operations, paths } from "./types.generated";
export {
  cancelBooking,
  createBooking,
  fetchBooking,
  fetchBookings,
  fetchMyBookings,
  type BookingsListParams,
} from "./bookings";
export {
  createOccurrence,
  deleteOccurrence,
  fetchOccurrence,
  fetchOccurrenceBookings,
  updateOccurrence,
} from "./occurrences";
export { createCheckoutSession } from "./payments";
export { fetchSearch } from "./search";
export {
  createStudio,
  deleteStudio,
  fetchStudio,
  fetchStudioOccurrences,
  fetchStudioServices,
  fetchStudios,
  updateStudio,
  type StudioOccurrencesParams,
  type StudiosListParams,
} from "./studios";
