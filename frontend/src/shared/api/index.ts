/** API client, domain fetchers, error helpers, and generated OpenAPI types.
 *
 * Client Components: import from `@shared/api`.
 * Server Components (public only): import from `@shared/api/server` —
 * do not re-export server helpers here (`client-only` would break RSC).
 */
export { ApiError } from "./api-error";
export {
  api,
  createIdempotencyKey,
  createRequestId,
  IDEMPOTENCY_KEY_HEADER,
  REQUEST_ID_HEADER,
  setAuthTokenProvider,
  setRefreshTokensFn,
  type AuthTokenProvider,
  type RefreshTokensFn,
  type RequestConfig,
} from "./client";
export { buildApiUrl, type QueryParamValue, type QueryParams } from "./build-url";
export { getUserFacingApiMessage } from "./error-message";
export { resolveRequestIdFromResponse } from "./request-headers";
export type { Schema } from "./schema";
export type { components, operations, paths } from "./types.generated";
export {
  cancelBooking,
  createBooking,
  fetchBooking,
  fetchBookings,
  fetchMyBookings,
  type BookingAccessOptions,
  type BookingsListParams,
  type MyBookingsParams,
} from "./bookings";
export {
  createOccurrence,
  deleteOccurrence,
  fetchOccurrence,
  fetchOccurrenceBookings,
  updateOccurrence,
} from "./occurrences";
export {
  createCheckoutSession,
  type CreateCheckoutSessionOptions,
} from "./payments";
export { fetchSearch } from "./search";
export { updateCurrentUser } from "./users";
export {
  createStudio,
  deleteStudio,
  fetchPublicServiceOccurrences,
  fetchStudio,
  fetchStudioOccurrences,
  fetchStudioServices,
  fetchStudios,
  updateStudio,
  type StudioOccurrencesParams,
  type StudiosListParams,
} from "./studios";
