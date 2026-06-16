/**
 * Bookings API.
 */

import { api } from "./client";
import type {
  BookingCreate,
  BookingCreatedResponse,
  BookingResponse,
  BookingSelfListItem,
} from "@/types/booking";

export interface BookingsListParams {
  skip?: number;
  limit?: number;
  occurrence_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export interface BookingsCountParams {
  occurrence_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export async function fetchBookings(
  params: BookingsListParams = {},
): Promise<BookingResponse[]> {
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

  return api.get<BookingResponse[]>("api/v1/bookings", {
    params: searchParams,
  });
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

  return api.get<BookingSelfListItem[]>("api/v1/bookings/my", {
    params: searchParams,
  });
}

export async function fetchBookingsCount(
  params: BookingsCountParams = {},
): Promise<{ count: number }> {
  const { occurrence_id, user_id, guest_email, status } = params;
  const searchParams: Record<string, string | number | undefined> = {};
  if (occurrence_id !== undefined) searchParams.occurrence_id = occurrence_id;
  if (user_id !== undefined) searchParams.user_id = user_id;
  if (guest_email) searchParams.guest_email = guest_email;
  if (status) searchParams.status = status;

  return api.get<{ count: number }>("api/v1/bookings/count", {
    params: searchParams,
  });
}

export async function fetchBooking(id: number): Promise<BookingResponse> {
  return api.get<BookingResponse>(`api/v1/bookings/${id}`, {
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

export async function cancelBooking(id: number): Promise<BookingResponse> {
  return api.patch<BookingResponse>(`api/v1/bookings/${id}/cancel`, undefined, {
    skipAuth: true,
  });
}
