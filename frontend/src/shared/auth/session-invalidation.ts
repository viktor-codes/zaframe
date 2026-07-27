/**
 * Bridge between the API client's refresh failure path and AuthProvider.
 *
 * WHY: refresh is wired once in bootstrapAuthClient (module scope) but
 * clearing the TanStack Query auth cache requires the React QueryClient
 * and loginTrigger — registered by AuthProvider via useLayoutEffect.
 */

type AuthSessionInvalidatedHandler = () => void;

let handler: AuthSessionInvalidatedHandler | null = null;

export function setAuthSessionInvalidatedHandler(
  next: AuthSessionInvalidatedHandler | null,
): void {
  handler = next;
}

export function notifyAuthSessionInvalidated(): void {
  handler?.();
}

/** Derive UI user from /auth/me query — never keep cached user after error. */
export function resolveAuthUserFromQuery<T>(
  data: T | undefined,
  isError: boolean,
): T | null {
  if (isError) return null;
  return data ?? null;
}
