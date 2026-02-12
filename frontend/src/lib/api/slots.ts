/**
 * API для слотов (расписание).
 */

import { api } from "./client";
import type { BookingResponse } from "@/types/booking";
import type { SlotCreate, SlotResponse, SlotUpdate } from "@/types/slot";

export async function fetchSlot(id: number): Promise<SlotResponse> {
  return api.get<SlotResponse>(`api/v1/slots/${id}`, {
    skipAuth: true,
  });
}

export async function createSlot(data: SlotCreate): Promise<SlotResponse> {
  return api.post<SlotResponse>("api/v1/slots", data);
}

export async function updateSlot(id: number, data: SlotUpdate): Promise<SlotResponse> {
  return api.patch<SlotResponse>(`api/v1/slots/${id}`, data);
}

export async function deleteSlot(id: number): Promise<void> {
  return api.delete<void>(`api/v1/slots/${id}`);
}

export async function fetchSlotBookings(
  slotId: number,
  params?: { skip?: number; limit?: number; status?: string }
): Promise<BookingResponse[]> {
  const { skip = 0, limit = 50, status } = params ?? {};
  const searchParams: Record<string, string | number | undefined> = {
    skip,
    limit,
  };
  if (status) searchParams.status = status;
  return api.get<BookingResponse[]>(`api/v1/slots/${slotId}/bookings`, {
    params: searchParams,
  });
}
