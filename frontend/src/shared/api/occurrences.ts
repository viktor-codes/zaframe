/**
 * Occurrence API (bookable time instances).
 */

import { api } from "./client";
import type {
  BookingOwnerResponse,
  PaginatedBookingOwnerList,
} from "@entities/booking";
import type {
  OccurrenceCreate,
  OccurrenceResponse,
  OccurrenceUpdate,
} from "@entities/occurrence";

const DEFAULT_PAGE = 1;
const DEFAULT_SIZE = 50;

export async function fetchOccurrence(id: number): Promise<OccurrenceResponse> {
  return api.get<OccurrenceResponse>(`api/v1/occurrences/${id}`, {
    skipAuth: true,
  });
}

export async function createOccurrence(
  data: OccurrenceCreate,
): Promise<OccurrenceResponse> {
  return api.post<OccurrenceResponse>("api/v1/occurrences", data);
}

export async function updateOccurrence(
  id: number,
  data: OccurrenceUpdate,
): Promise<OccurrenceResponse> {
  return api.patch<OccurrenceResponse>(`api/v1/occurrences/${id}`, data);
}

export async function deleteOccurrence(id: number): Promise<void> {
  return api.delete<void>(`api/v1/occurrences/${id}`);
}

export async function fetchOccurrenceBookings(
  occurrenceId: number,
  params?: { page?: number; size?: number; status?: string },
): Promise<BookingOwnerResponse[]> {
  const {
    page = DEFAULT_PAGE,
    size = DEFAULT_SIZE,
    status,
  } = params ?? {};
  const searchParams: Record<string, string | number | undefined> = {
    page,
    size,
  };
  if (status) searchParams.status = status;
  const response = await api.get<PaginatedBookingOwnerList>(
    `api/v1/occurrences/${occurrenceId}/bookings`,
    {
      params: searchParams,
    },
  );
  return response.items;
}
