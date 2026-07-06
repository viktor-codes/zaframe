import type { Schema } from "@shared/api/schema";

export type ServiceResponse = Schema<"ServiceResponse">;
export type ServiceCreate = Schema<"ServiceCreate">;
export type ServiceUpdate = Schema<"ServiceUpdate">;
export type ServiceCategory = Schema<"ServiceCategory">;
export type PublicService = Schema<"PublicService">;
export type ServiceAvailabilityResponse = Schema<"ServiceAvailabilityResponse">;
export type ServiceAvailabilityScheduleItem =
  Schema<"ServiceAvailabilityScheduleItem">;
export type PaginatedServiceList = Schema<"PaginatedResponse_ServiceResponse_">;

export type ServiceVisibility = ServiceResponse["visibility"];
export type ServiceType = ServiceResponse["type"];
