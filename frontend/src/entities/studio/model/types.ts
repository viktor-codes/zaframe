import type { operations } from "@shared/api/types.generated";
import type { Schema } from "@shared/api/schema";

export type StudioResponse = Schema<"StudioResponse">;
export type SearchResult = Schema<"SearchResult">;
export type SearchQueryParams = NonNullable<
  operations["search_endpoint_api_v1_search_get"]["parameters"]["query"]
>;
/** Query params for `GET /studios` — from OpenAPI operation. */
export type StudiosListParams = NonNullable<
  operations["list_studios_api_v1_studios_get"]["parameters"]["query"]
>;
export type StudioCreate = Schema<"StudioCreate">;
export type StudioUpdate = Schema<"StudioUpdate">;
export type StudioPublicResponse = Schema<"StudioPublicResponse">;
export type StudioWithRoleResponse = Schema<"StudioWithRoleResponse">;
export type PaginatedStudioList = Schema<"PaginatedResponse_StudioResponse_">;
export type PaginatedStudioWithRoleList =
  Schema<"PaginatedResponse_StudioWithRoleResponse_">;
export type PaginatedSearchResultList =
  Schema<"PaginatedResponse_SearchResult_">;
