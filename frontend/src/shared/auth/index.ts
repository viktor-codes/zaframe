/** Auth context, storage, role/permission hooks, and route guards.
 *
 * WHY: do not re-export `./api` here — it is `client-only` and would break
 * Server Component imports of guards (e.g. RequireAuth in app layouts).
 * Session helpers: import from `@shared/auth/api` in Client Components only.
 */
export { AuthProvider, useAuth } from "./context";
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
  RequireStudioPermission,
  type RequireStudioPermissionProps,
} from "./require-studio-permission";
export {
  canStudioPermission,
  hasStudioRole,
  resolveStudioRole,
} from "./resolve-studio-access";
