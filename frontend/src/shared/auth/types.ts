import type { components } from "@shared/api";

/** Current user from GET /auth/me (includes studio-scoped roles). */
export type AuthUser = components["schemas"]["CurrentUserResponse"];

export interface AuthState {
  user: AuthUser | null;
  isInitialized: boolean;
}

export interface AuthActions {
  /** Store the access token and refetch the current user from /auth/me. */
  login: (accessToken: string) => void;
  logout: () => void;
  /**
   * Drop local tokens and private caches without calling /auth/logout.
   * Use after delete-account (server already revoked sessions and cookies).
   */
  clearSession: () => void;
}
