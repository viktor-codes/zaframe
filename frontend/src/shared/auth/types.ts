import type { components } from "@shared/api";

/** Current user from GET /auth/me (includes studio-scoped roles). */
export type AuthUser = components["schemas"]["CurrentUserResponse"];

/** User payload returned by magic-link verify before /auth/me refetch. */
export type LoginUser = components["schemas"]["UserResponse"];

export interface AuthState {
  user: AuthUser | null;
  isInitialized: boolean;
}

export interface AuthActions {
  login: (accessToken: string, user: LoginUser) => void;
  logout: () => void;
}
