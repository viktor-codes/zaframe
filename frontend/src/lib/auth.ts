/**
 * @deprecated Import from `@shared/auth` — kept for gradual migration.
 */
export {
  AuthProvider,
  useAuth,
  clearStoredTokens,
  getStoredAccessToken,
  getStoredRefreshToken,
  logoutSession,
  refreshAccessToken,
  setStoredTokens,
} from "@shared/auth";
export type {
  AuthActions,
  AuthState,
  AuthUser,
  LoginUser,
} from "@shared/auth";
