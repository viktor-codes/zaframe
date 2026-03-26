/**
 * Типы для auth контекста.
 */

import type { UserResponse } from "@/types";

export interface AuthState {
  user: UserResponse | null;
  isInitialized: boolean;
}

export interface AuthActions {
  login: (accessToken: string, user: UserResponse) => void;
  logout: () => void;
}
