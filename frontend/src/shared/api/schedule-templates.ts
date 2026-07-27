/**
 * Schedule template API (recurring rules → generate occurrences).
 */

import type {
  PaginatedScheduleTemplateList,
  ScheduleTemplateCreate,
  ScheduleTemplateResponse,
  ScheduleTemplateUpdate,
} from "@entities/schedule-template";

import { api } from "./client";

export async function fetchServiceScheduleTemplates(
  serviceId: number,
): Promise<ScheduleTemplateResponse[]> {
  const response = await api.get<PaginatedScheduleTemplateList>(
    `api/v1/services/${serviceId}/schedule-templates`,
  );
  return response.items;
}

export async function createScheduleTemplate(
  serviceId: number,
  data: ScheduleTemplateCreate,
): Promise<ScheduleTemplateResponse> {
  return api.post<ScheduleTemplateResponse>(
    `api/v1/services/${serviceId}/schedule-templates`,
    data,
  );
}

export async function updateScheduleTemplate(
  scheduleTemplateId: number,
  data: ScheduleTemplateUpdate,
): Promise<ScheduleTemplateResponse> {
  return api.patch<ScheduleTemplateResponse>(
    `api/v1/services/schedule-templates/${scheduleTemplateId}`,
    data,
  );
}

export async function deleteScheduleTemplate(
  scheduleTemplateId: number,
): Promise<void> {
  return api.delete<void>(
    `api/v1/services/schedule-templates/${scheduleTemplateId}`,
  );
}
