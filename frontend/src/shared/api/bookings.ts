/**
 * Bookings API.
 */

import { api } from "./client";
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
  skip?: number;
  limit?: number;
  occurrence_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export async function fetchBookings(
  params: BookingsListParams = {},
): Promise<BookingOwnerResponse[]> {
  const {
    skip = 0,
    limit = 20,
    occurrence_id,
    user_id,
    guest_email,
    status,
  } = params;
  const searchParams: Record<string, string | number | undefined> = {
    skip,
    limit,
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
  skip?: number;
  limit?: number;
  include_guest_email?: boolean;
}): Promise<BookingSelfListItem[]> {
  const searchParams: Record<string, string | number | boolean | undefined> = {};
  if (params?.skip !== undefined) searchParams.skip = params.skip;
  if (params?.limit !== undefined) searchParams.limit = params.limit;
  if (params?.include_guest_email !== undefined)
    searchParams.include_guest_email = params.include_guest_email;

  const response = await api.get<PaginatedBookingSelfList>("api/v1/bookings/my", {
    params: searchParams,
  });
  return response.items;
}

export async function fetchBooking(
  id: number,
): Promise<BookingDetailResponse> {
  return api.get<BookingDetailResponse>(`api/v1/bookings/${id}`, {
    skipAuth: true,
  });
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
): Promise<BookingDetailResponse> {
  return api.patch<BookingDetailResponse>(
    `api/v1/bookings/${id}/cancel`,
    undefined,
    {
      skipAuth: true,
    },
  );
}
