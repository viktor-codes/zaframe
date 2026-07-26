/**
 * Service catalog API (dashboard CRUD).
 */

import type {
  ServiceCreate,
  ServiceResponse,
  ServiceUpdate,
} from "@entities/service";

import { api } from "./client";

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
