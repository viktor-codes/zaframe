import type { operations } from "@shared/api/types.generated";
import type { Schema } from "@shared/api/schema";

export type OccurrenceResponse = Schema<"OccurrenceResponse">;
export type OccurrenceCreate = Schema<"OccurrenceCreate">;
export type OccurrenceUpdate = Schema<"OccurrenceUpdate">;
export type OccurrenceInstructorResponse =
  Schema<"OccurrenceInstructorResponse">;
export type PaginatedOccurrenceList =
  Schema<"PaginatedResponse_OccurrenceResponse_">;

/** Query params for `GET /studios/{id}/occurrences` — from OpenAPI operation. */
export type StudioOccurrencesParams = NonNullable<
  operations["list_studio_occurrences_api_v1_studios__studio_id__occurrences_get"]["parameters"]["query"]
>;

export type OccurrenceStatus = OccurrenceResponse["status"];
