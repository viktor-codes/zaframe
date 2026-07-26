import type { operations } from "@shared/api/types.generated";
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

/** Query params for `GET /studios/{id}/services` — from OpenAPI operation. */
export type StudioServicesParams = NonNullable<
  operations["list_studio_services_endpoint_api_v1_studios__studio_id__services_get"]["parameters"]["query"]
>;

export type ServiceVisibility = ServiceResponse["visibility"];
export type ServiceType = ServiceResponse["type"];
