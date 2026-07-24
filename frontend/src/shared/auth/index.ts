/** Auth context, storage, session API, role/permission hooks, and route guards. */
export { AuthProvider, useAuth } from "./context";
export { logoutSession, refreshAccessToken } from "./api";
export {
  clearStoredTokens,
  getStoredAccessToken,
  setStoredTokens,
} from "./storage";
export type { AuthActions, AuthState, AuthUser } from "./types";
export { useRole } from "./use-role";
export { usePermission, type UsePermissionResult } from "./use-permission";
export { RequireAuth, type RequireAuthProps } from "./require-auth";
export {
  RequireStudioRole,
  type RequireStudioRoleProps,
} from "./require-studio-role";
export {
  canStudioPermission,
  hasStudioRole,
  resolveStudioRole,
} from "./resolve-studio-access";
