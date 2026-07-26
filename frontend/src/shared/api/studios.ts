/**
 * Studio API.
 */

import { api } from "./client";
import type {
  OccurrenceResponse,
  PaginatedOccurrenceList,
} from "@entities/occurrence";
import type { PaginatedServiceList, ServiceResponse } from "@entities/service";
import type {
  PaginatedSearchResultList,
  PaginatedStudioList,
  StudioCreate,
  StudioResponse,
  StudioUpdate,
} from "@entities/studio";

export interface StudiosListParams {
  page?: number;
  size?: number;
  owner_id?: number;
  is_active?: boolean;
  city?: string;
  category?: string;
  query?: string;
  amenities?: string[];
  include_services?: boolean;
}

export interface StudioOccurrencesParams {
  page?: number;
  size?: number;
  start_from?: string;
  start_to?: string;
  status?: "scheduled" | "cancelled" | "completed";
}

const DEFAULT_PAGE = 1;
const DEFAULT_STUDIO_PAGE_SIZE = 12;
const DEFAULT_OCCURRENCE_PAGE_SIZE = 50;

export async function fetchStudios(
  params: StudiosListParams = {},
): Promise<PaginatedStudioList | PaginatedSearchResultList> {
  const {
    page = DEFAULT_PAGE,
    size = DEFAULT_STUDIO_PAGE_SIZE,
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
    page,
    size,
  };
  if (owner_id !== undefined) searchParams.owner_id = owner_id;
  if (is_active !== undefined) searchParams.is_active = is_active;
  if (city) searchParams.city = city;
  if (category) searchParams.category = category;
  if (query) searchParams.query = query;
  if (amenities?.length) searchParams.amenities = amenities;
  if (include_services === true) searchParams.include_services = true;

  return api.get<PaginatedStudioList | PaginatedSearchResultList>(
    "api/v1/studios",
    {
      params: searchParams,
      skipAuth: !owner_id,
    },
  );
}

export async function createStudio(
  data: Omit<StudioCreate, "owner_id">,
): Promise<StudioResponse> {
  return api.post<StudioResponse>("api/v1/studios", data);
}

export async function updateStudio(
  id: number,
  data: StudioUpdate,
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

export async function fetchStudioServices(
  studioId: number,
  params?: { page?: number; size?: number },
): Promise<ServiceResponse[]> {
  const response = await api.get<PaginatedServiceList>(
    `api/v1/studios/${studioId}/services`,
    {
      params: {
        page: params?.page ?? DEFAULT_PAGE,
        size: params?.size ?? 100,
      },
    },
  );
  return response.items;
}

export async function fetchStudioOccurrences(
  studioId: number,
  params: StudioOccurrencesParams = {},
): Promise<OccurrenceResponse[]> {
  const {
    page = DEFAULT_PAGE,
    size = DEFAULT_OCCURRENCE_PAGE_SIZE,
    start_from,
    start_to,
    status,
  } = params;
  const searchParams: Record<string, string | number | boolean | undefined> = {
    page,
    size,
  };
  if (start_from) searchParams.start_from = start_from;
  if (start_to) searchParams.start_to = start_to;
  if (status !== undefined) searchParams.status = status;

  const response = await api.get<PaginatedOccurrenceList>(
    `api/v1/studios/${studioId}/occurrences`,
    {
      params: searchParams,
      skipAuth: true,
    },
  );
  return response.items;
}
