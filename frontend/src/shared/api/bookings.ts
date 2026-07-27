/**
 * Bookings API.
 */

import { api, type RequestConfig } from "./client";
import type {
  BookingCreate,
  BookingCreatedResponse,
  BookingDetailResponse,
  BookingOwnerResponse,
  CourseBookingCreate,
  CourseBookingResponse,
  PaginatedBookingSelfList,
  PaginatedBookingWithOccurrenceList,
} from "@entities/booking";
import type { BookingStatus } from "@shared/lib/constants";

export interface BookingsListParams {
  page?: number;
  size?: number;
  /** Recommended for studio dashboard; requires view_bookings. */
  studio_id?: number;
  occurrence_id?: number;
  status?: BookingStatus;
}

/** Query params for GET /bookings/my (page is supplied by infinite-query pageParam). */
export interface MyBookingsParams {
  page?: number;
  size?: number;
  include_guest_email?: boolean;
}

export interface BookingAccessOptions {
  /**
   * Guest JWT from POST /bookings (sessionStorage on confirm page).
   * When set, sent as Bearer and session refresh is skipped.
   */
  accessToken?: string | null;
  /** TanStack Query (or caller) cancellation signal. */
  signal?: AbortSignal;
}

function bookingAuthConfig(options?: BookingAccessOptions): RequestConfig {
  const config: RequestConfig = {};
  if (options?.signal) {
    config.signal = options.signal;
  }
  const accessToken = options?.accessToken;
  if (accessToken) {
    return {
      ...config,
      skipAuth: true,
      skipRefresh: true,
      headers: { Authorization: `Bearer ${accessToken}` },
    };
  }
  return config;
}

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 20;

/**
 * Studio-staff bookings list (paginated envelope + nested occurrence).
 * WHY: callers need `total` for pagination and occurrence for session context.
 */
export async function fetchBookings(
  params: BookingsListParams = {},
): Promise<PaginatedBookingWithOccurrenceList> {
  const {
    page = DEFAULT_PAGE,
    size = DEFAULT_SIZE,
    studio_id,
    occurrence_id,
    status,
  } = params;
  const searchParams: Record<string, string | number | undefined> = {
    page,
    size,
  };
  if (studio_id !== undefined) searchParams.studio_id = studio_id;
  if (occurrence_id !== undefined) searchParams.occurrence_id = occurrence_id;
  if (status) searchParams.status = status;

  return api.get<PaginatedBookingWithOccurrenceList>("api/v1/bookings", {
    params: searchParams,
  });
}

/**
 * List current-user bookings (paginated envelope).
 * WHY: callers need `total` / `page` / `size` for account infinite scroll.
 */
export async function fetchMyBookings(
  params: MyBookingsParams = {},
): Promise<PaginatedBookingSelfList> {
  const searchParams: Record<string, string | number | boolean | undefined> = {
    page: params.page ?? DEFAULT_PAGE,
    size: params.size ?? DEFAULT_SIZE,
  };
  if (params.include_guest_email !== undefined) {
    searchParams.include_guest_email = params.include_guest_email;
  }

  return api.get<PaginatedBookingSelfList>("api/v1/bookings/my", {
    params: searchParams,
  });
}

export async function fetchBooking(
  id: number,
  options?: BookingAccessOptions,
): Promise<BookingDetailResponse> {
  return api.get<BookingDetailResponse>(
    `api/v1/bookings/${id}`,
    bookingAuthConfig(options),
  );
}

export async function createBooking(
  data: BookingCreate,
): Promise<BookingCreatedResponse> {
  // WHY: send Bearer when present so the API can attach user_id immediately;
  // guests without a token still create anonymously (optional auth on backend).
  return api.post<BookingCreatedResponse>("api/v1/bookings", data);
}

/**
 * Course purchase: one Order + N bookings (`CourseBookingCreate`).
 * WHY: same path as single booking, but response shape is order-centric
 * (access_token pays the order, not a single booking).
 */
export async function createCourseBooking(
  data: CourseBookingCreate,
): Promise<CourseBookingResponse> {
  return api.post<CourseBookingResponse>("api/v1/bookings", data);
}

export async function cancelBooking(
  id: number,
  options?: BookingAccessOptions,
): Promise<BookingDetailResponse> {
  return api.patch<BookingDetailResponse>(
    `api/v1/bookings/${id}/cancel`,
    undefined,
    bookingAuthConfig(options),
  );
}

/**
 * Mark attendee as checked in (`PATCH /bookings/{id}/check-in`).
 * Requires `check_in_booking`; idempotent when already checked in.
 */
export async function checkInBooking(
  id: number,
): Promise<BookingOwnerResponse> {
  return api.patch<BookingOwnerResponse>(`api/v1/bookings/${id}/check-in`);
}

/**
 * Mark attendee as no-show (`PATCH /bookings/{id}/mark-no-show`).
 * Requires `check_in_booking`; blocked after check-in.
 */
export async function markBookingNoShow(
  id: number,
): Promise<BookingOwnerResponse> {
  return api.patch<BookingOwnerResponse>(
    `api/v1/bookings/${id}/mark-no-show`,
  );
}
