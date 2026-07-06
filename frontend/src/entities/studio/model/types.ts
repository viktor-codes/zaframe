import type { Schema } from "@shared/api/schema";

export type StudioResponse = Schema<"StudioResponse">;
export type StudioCreate = Schema<"StudioCreate">;
export type StudioUpdate = Schema<"StudioUpdate">;
export type StudioPublicResponse = Schema<"StudioPublicResponse">;
export type StudioWithRoleResponse = Schema<"StudioWithRoleResponse">;
export type StudioRoleResponse = Schema<"StudioRoleResponse">;
export type PaginatedStudioList = Schema<"PaginatedResponse_StudioResponse_">;
export type PaginatedStudioWithRoleList =
  Schema<"PaginatedResponse_StudioWithRoleResponse_">;
