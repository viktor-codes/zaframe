import type { Schema } from "@shared/api/schema";

export type OccurrenceResponse = Schema<"OccurrenceResponse">;
export type OccurrenceCreate = Schema<"OccurrenceCreate">;
export type OccurrenceUpdate = Schema<"OccurrenceUpdate">;
export type OccurrenceInstructorResponse = Schema<"OccurrenceInstructorResponse">;
export type PaginatedOccurrenceList =
  Schema<"PaginatedResponse_OccurrenceResponse_">;

export type OccurrenceStatus = OccurrenceResponse["status"];
