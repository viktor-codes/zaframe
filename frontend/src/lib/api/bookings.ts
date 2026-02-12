/**
 * API для бронирований.
 */

import { api } from "./client";
import type { BookingCreate, BookingResponse } from "@/types/booking";

export interface BookingsListParams {
  skip?: number;
  limit?: number;
  slot_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export interface BookingsCountParams {
  slot_id?: number;
  user_id?: number;
  guest_email?: string;
  status?: string;
}

export async function fetchBookings(
  params: BookingsListParams = {}
): Promise<BookingResponse[]> {
  const { skip = 0, limit = 20, slot_id, user_id, guest_email, status } = params;
  const searchParams: Record<string, string | number | undefined> = {
    skip,
    limit,
  };
  if (slot_id !== undefined) searchParams.slot_id = slot_id;
  if (user_id !== undefined) searchParams.user_id = user_id;
  if (guest_email) searchParams.guest_email = guest_email;
  if (status) searchParams.status = status;

  return api.get<BookingResponse[]>("api/v1/bookings", {
    params: searchParams,
  });
}

export async function fetchBookingsCount(
  params: BookingsCountParams = {}
): Promise<{ count: number }> {
  const { slot_id, user_id, guest_email, status } = params;
  const searchParams: Record<string, string | number | undefined> = {};
  if (slot_id !== undefined) searchParams.slot_id = slot_id;
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

export async function createBooking(data: BookingCreate): Promise<BookingResponse> {
  return api.post<BookingResponse>("api/v1/bookings", data, {
    skipAuth: true,
  });
}

export async function cancelBooking(id: number): Promise<BookingResponse> {
  return api.patch<BookingResponse>(`api/v1/bookings/${id}/cancel`, undefined, {
    skipAuth: true,
  });
}
