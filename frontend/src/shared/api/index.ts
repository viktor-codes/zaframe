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
  checkInBooking,
  createBooking,
  createCourseBooking,
  fetchBooking,
  fetchBookings,
  fetchMyBookings,
  markBookingNoShow,
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
  createOrderCheckoutSession,
  createStudioStripeOnboarding,
  fetchStudioPayoutSettings,
  fetchStudioStripeStatus,
  updateStudioPayoutSettings,
  type CreateCheckoutSessionOptions,
  type PayoutSettingsUpdate,
  type StripeConnectOnboardCreate,
  type StripeConnectOnboardResponse,
  type StripeConnectStatusResponse,
} from "./payments";
export { fetchSearch } from "./search";
export {
  createService,
  deactivateService,
  fetchService,
  fetchServiceAvailability,
  updateService,
  type ServiceAvailabilityParams,
} from "./services";
export {
  createScheduleTemplate,
  deleteScheduleTemplate,
  fetchServiceScheduleTemplates,
  updateScheduleTemplate,
} from "./schedule-templates";
export { fetchMyOrders, fetchOrder, type MyOrdersParams, type OrderAccessOptions } from "./orders";
export { updateCurrentUser } from "./users";
export {
  createStudio,
  deleteStudio,
  fetchMyStudios,
  fetchPublicServiceOccurrences,
  fetchStudio,
  fetchStudioOccurrences,
  generateStudioOccurrences,
  fetchStudioServices,
  fetchStudios,
  updateStudio,
  type StudioOccurrencesParams,
  type StudioServicesParams,
  type StudiosListParams,
} from "./studios";
