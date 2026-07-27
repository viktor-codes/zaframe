/**
 * Current-user profile API (identity / auth me).
 */

import type { CurrentUserUpdate, UserResponse } from "@entities/user";
import type { components } from "./types.generated";
import { api } from "./client";

export type UserDataExport = components["schemas"]["UserDataExportResponse"];

/** PATCH /auth/me — editable profile fields only (not email). */
export async function updateCurrentUser(
  data: CurrentUserUpdate,
): Promise<UserResponse> {
  return api.patch<UserResponse>("api/v1/auth/me", data);
}

/** POST /me/delete-account — soft-delete; API clears refresh cookies. */
export async function deleteCurrentUserAccount(): Promise<void> {
  await api.post<void>("api/v1/me/delete-account");
}

/** GET /me/export — GDPR DSAR JSON envelope. */
export async function getCurrentUserExport(): Promise<UserDataExport> {
  return api.get<UserDataExport>("api/v1/me/export");
}
