/**
 * Service catalog API (dashboard CRUD + public availability).
 */

import type {
  ServiceAvailabilityResponse,
  ServiceCreate,
  ServiceResponse,
  ServiceUpdate,
} from "@entities/service";

import { api } from "./client";

export interface ServiceAvailabilityParams {
  /** Optional start date (YYYY-MM-DD); backend defaults to today. */
  start_date?: string | null;
  signal?: AbortSignal;
}

/**
 * Public course availability for purchase warnings (overbooked dates).
 * WHY: storefront must warn before course checkout (STRATEGY §7).
 */
export async function fetchServiceAvailability(
  serviceId: number,
  params: ServiceAvailabilityParams = {},
): Promise<ServiceAvailabilityResponse> {
  const searchParams: Record<string, string | undefined> = {};
  if (params.start_date != null && params.start_date !== "") {
    searchParams.start_date = params.start_date;
  }

  return api.get<ServiceAvailabilityResponse>(
    `api/v1/services/${serviceId}/availability`,
    {
      skipAuth: true,
      params: searchParams,
      signal: params.signal,
    },
  );
}

export async function fetchService(
  serviceId: number,
): Promise<ServiceResponse> {
  return api.get<ServiceResponse>(`api/v1/services/${serviceId}`);
}

export async function createService(
  data: ServiceCreate,
): Promise<ServiceResponse> {
  return api.post<ServiceResponse>("api/v1/services", data);
}

export async function updateService(
  serviceId: number,
  data: ServiceUpdate,
): Promise<ServiceResponse> {
  return api.patch<ServiceResponse>(`api/v1/services/${serviceId}`, data);
}

/**
 * Soft-delete: archives the service (`visibility=archived`, `is_active=false`).
 */
export async function deactivateService(
  serviceId: number,
): Promise<ServiceResponse> {
  return api.delete<ServiceResponse>(`api/v1/services/${serviceId}`);
}
