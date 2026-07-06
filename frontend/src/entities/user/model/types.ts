import type { Schema } from "@shared/api/schema";

export type UserResponse = Schema<"UserResponse">;
export type CurrentUserResponse = Schema<"CurrentUserResponse">;
export type CurrentUserUpdate = Schema<"CurrentUserUpdate">;
export type StudioRoleResponse = Schema<"StudioRoleResponse">;

export type UserProfile = Pick<
  CurrentUserResponse,
  "id" | "email" | "name" | "phone" | "role" | "roles"
>;
