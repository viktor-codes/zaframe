/**
 * Current-user profile API (identity / auth me).
 */

import type { CurrentUserUpdate, UserResponse } from "@entities/user";
import { api } from "./client";

/** PATCH /auth/me — editable profile fields only (not email). */
export async function updateCurrentUser(
  data: CurrentUserUpdate,
): Promise<UserResponse> {
  return api.patch<UserResponse>("api/v1/auth/me", data);
}
