/**
 * Bookings API.
 */

import { api, type RequestConfig } from "./client";
import type {
  BookingCreate,
  BookingCreatedResponse,
  BookingDetailResponse,
  BookingOwnerResponse,
  BookingSelfListItem,
  PaginatedBookingOwnerList,
  PaginatedBookingSelfList,
} from "@entities/booking";

export interface BookingsListParams {
  page?: number;
  size?: number;
  occurrence_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export interface BookingAccessOptions {
  /**
   * Guest JWT from POST /bookings (sessionStorage on confirm page).
   * When set, sent as Bearer and session refresh is skipped.
   */
  accessToken?: string | null;
}

function bookingAuthConfig(options?: BookingAccessOptions): RequestConfig {
  const accessToken = options?.accessToken;
  if (accessToken) {
    return {
      skipAuth: true,
      skipRefresh: true,
      headers: { Authorization: `Bearer ${accessToken}` },
    };
  }
  return {};
}

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 20;

export async function fetchBookings(
  params: BookingsListParams = {},
): Promise<BookingOwnerResponse[]> {
  const {
    page = DEFAULT_PAGE,
    size = DEFAULT_SIZE,
    occurrence_id,
    user_id,
    guest_email,
    status,
  } = params;
  const searchParams: Record<string, string | number | undefined> = {
    page,
    size,
  };
  if (occurrence_id !== undefined) searchParams.occurrence_id = occurrence_id;
  if (user_id !== undefined) searchParams.user_id = user_id;
  if (guest_email) searchParams.guest_email = guest_email;
  if (status) searchParams.status = status;

  const response = await api.get<PaginatedBookingOwnerList>("api/v1/bookings", {
    params: searchParams,
  });
  return response.items;
}

export async function fetchMyBookings(params?: {
  page?: number;
  size?: number;
  include_guest_email?: boolean;
}): Promise<BookingSelfListItem[]> {
  const searchParams: Record<string, string | number | boolean | undefined> = {
    page: params?.page ?? DEFAULT_PAGE,
    size: params?.size ?? DEFAULT_SIZE,
  };
  if (params?.include_guest_email !== undefined)
    searchParams.include_guest_email = params.include_guest_email;

  const response = await api.get<PaginatedBookingSelfList>("api/v1/bookings/my", {
    params: searchParams,
  });
  return response.items;
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
  return api.post<BookingCreatedResponse>("api/v1/bookings", data, {
    skipAuth: true,
  });
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
