import type { Schema } from "@shared/api/schema";

export type ScheduleTemplateResponse = Schema<"ScheduleTemplateResponse">;
/** Create body — OpenAPI uses `ScheduleTemplateBase` (no separate Create schema). */
export type ScheduleTemplateCreate = Schema<"ScheduleTemplateBase">;
export type ScheduleTemplateUpdate = Schema<"ScheduleTemplateUpdate">;
export type ScheduleGenerateRequest = Schema<"ScheduleGenerateRequest">;
export type PaginatedScheduleTemplateList =
  Schema<"PaginatedResponse_ScheduleTemplateResponse_">;
