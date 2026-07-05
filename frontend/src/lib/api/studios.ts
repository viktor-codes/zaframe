/**
 * Studio API.
 */

import { api } from "@shared/api";
import type { StudioCreate, StudioResponse } from "@/types/studio";
import type { OccurrenceResponse } from "@/types/occurrence";
import type { SearchResult } from "@/types/search";

export interface StudiosListParams {
  skip?: number;
  limit?: number;
  owner_id?: number;
  is_active?: boolean;
  city?: string;
  category?: string;
  query?: string;
  amenities?: string[];
  include_services?: boolean;
}

export interface StudiosCountParams {
  owner_id?: number;
  is_active?: boolean;
  city?: string;
  category?: string;
  query?: string;
  amenities?: string[];
}

export interface StudioOccurrencesParams {
  skip?: number;
  limit?: number;
  start_from?: string;
  start_to?: string;
  status?: "active" | "cancelled";
}

const PAGE_SIZE = 12;

export async function fetchStudios(
  params: StudiosListParams = {},
): Promise<StudioResponse[] | SearchResult[]> {
  const {
    skip = 0,
    limit = PAGE_SIZE,
    owner_id,
    is_active,
    city,
    category,
    query,
    amenities,
    include_services,
  } = params;
  const searchParams: Record<
    string,
    string | number | boolean | string[] | undefined
  > = {
    skip,
    limit,
  };
  if (owner_id !== undefined) searchParams.owner_id = owner_id;
  if (is_active !== undefined) searchParams.is_active = is_active;
  if (city) searchParams.city = city;
  if (category) searchParams.category = category;
  if (query) searchParams.query = query;
  if (amenities?.length) searchParams.amenities = amenities;
  if (include_services === true) searchParams.include_services = true;

  return api.get<StudioResponse[] | SearchResult[]>("api/v1/studios", {
    params: searchParams,
    skipAuth: !owner_id,
  });
}

export async function fetchStudiosCount(
  params: StudiosCountParams = {},
): Promise<{ count: number }> {
  const { owner_id, is_active, city, category, query, amenities } = params;
  const searchParams: Record<
    string,
    string | number | boolean | string[] | undefined
  > = {};
  if (owner_id !== undefined) searchParams.owner_id = owner_id;
  if (is_active !== undefined) searchParams.is_active = is_active;
  if (city) searchParams.city = city;
  if (category) searchParams.category = category;
  if (query) searchParams.query = query;
  if (amenities?.length) searchParams.amenities = amenities;

  return api.get<{ count: number }>("api/v1/studios/count", {
    params: searchParams,
    skipAuth: !owner_id,
  });
}

export async function createStudio(
  data: Omit<StudioCreate, "owner_id">,
): Promise<StudioResponse> {
  return api.post<StudioResponse>("api/v1/studios", data);
}

export async function updateStudio(
  id: number,
  data: Partial<{
    name: string;
    description: string | null;
    email: string | null;
    phone: string | null;
    address: string | null;
    is_active: boolean;
  }>,
): Promise<StudioResponse> {
  return api.patch<StudioResponse>(`api/v1/studios/${id}`, data);
}

export async function deleteStudio(id: number): Promise<void> {
  return api.delete<void>(`api/v1/studios/${id}`);
}

export async function fetchStudio(id: number): Promise<StudioResponse> {
  return api.get<StudioResponse>(`api/v1/studios/${id}`, {
    skipAuth: true,
  });
}

export async function fetchStudioOccurrences(
  studioId: number,
  params: StudioOccurrencesParams = {},
): Promise<OccurrenceResponse[]> {
  const { skip = 0, limit = 50, start_from, start_to, status } = params;
  const searchParams: Record<string, string | number | boolean | undefined> = {
    skip,
    limit,
  };
  if (start_from) searchParams.start_from = start_from;
  if (start_to) searchParams.start_to = start_to;
  if (status !== undefined) searchParams.status = status;

  return api.get<OccurrenceResponse[]>(
    `api/v1/studios/${studioId}/occurrences`,
    {
      params: searchParams,
      skipAuth: true,
    },
  );
}
