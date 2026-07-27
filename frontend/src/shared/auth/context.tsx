"use client";

/**
 * Auth context and provider.
 *
 * - Wires API client with getAccessToken and refreshTokens
 * - Exposes user, login, logout
 * - User is loaded via TanStack Query when a token is present
 * - Failed refresh clears tokens + auth query cache (no ghost session)
 */

import {
  createContext,
  useCallback,
  useContext,
  useLayoutEffect,
  useMemo,
  useState,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, setAuthTokenProvider, setRefreshTokensFn } from "@shared/api";
import { queryKeys } from "@shared/lib/query-keys";
import { clearPrivateClientSession } from "@shared/lib/clear-private-client-session";
import { logoutSession, refreshAccessToken } from "./api";
import {
  notifyAuthSessionInvalidated,
  resolveAuthUserFromQuery,
  setAuthSessionInvalidatedHandler,
} from "./session-invalidation";
import {
  clearStoredTokens,
  getStoredAccessToken,
  setStoredTokens,
} from "./storage";
import type { AuthActions, AuthState, AuthUser } from "./types";

type AuthContextValue = AuthState & AuthActions;

const AuthContext = createContext<AuthContextValue | null>(null);

let isAuthClientBootstrapped = false;

/**
 * Wire the shared API client to auth storage and token refresh.
 *
 * Runs once, synchronously, before the first `/auth/me` query so a returning
 * user (whose access token is memory-only and lost on reload) gets a
 * refresh-driven retry on the initial 401 instead of appearing logged out.
 */
function bootstrapAuthClient(): void {
  if (isAuthClientBootstrapped) {
    return;
  }
  isAuthClientBootstrapped = true;

  // Migration: access token is memory-only now, drop any persisted token.
  try {
    window.localStorage.removeItem("zeeframe_access_token");
  } catch {
    // ignore storage errors (private mode, denied, etc.)
  }

  setAuthTokenProvider(getStoredAccessToken);
  setRefreshTokensFn(async () => {
    try {
      const res = await refreshAccessToken();
      setStoredTokens(res.access_token);
      return { access_token: res.access_token };
    } catch {
      clearStoredTokens();
      // WHY: TQ keeps previous /auth/me data on error — force logged-out UI.
      notifyAuthSessionInvalidated();
      return null;
    }
  });
}

function useAuthQuery(loginTrigger: number, isReady: boolean) {
  return useQuery({
    queryKey: queryKeys.auth.me(loginTrigger),
    queryFn: ({ signal }) =>
      api.get<AuthUser>("/api/v1/auth/me", { signal }),
    enabled: isReady,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const queryClient = useQueryClient();
  const [loginTrigger, setLoginTrigger] = useState(0);
  const [isBootstrapped] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    bootstrapAuthClient();
    return true;
  });

  const clearAuthSession = useCallback(() => {
    clearStoredTokens();
    clearPrivateClientSession(queryClient);
    setLoginTrigger((prev) => prev + 1);
  }, [queryClient]);

  useLayoutEffect(() => {
    setAuthSessionInvalidatedHandler(() => {
      clearPrivateClientSession(queryClient);
      setLoginTrigger((prev) => prev + 1);
    });
    return () => setAuthSessionInvalidatedHandler(null);
  }, [queryClient]);

  const { data: user, isLoading, isError } = useAuthQuery(
    loginTrigger,
    isBootstrapped,
  );

  const login = useCallback((accessToken: string) => {
    setStoredTokens(accessToken);
    setAuthTokenProvider(getStoredAccessToken);
    setLoginTrigger((prev) => prev + 1);
  }, []);

  const logout = useCallback(() => {
    void logoutSession().finally(() => {
      clearAuthSession();
    });
  }, [clearAuthSession]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: resolveAuthUserFromQuery(user, isError),
      isInitialized: isBootstrapped && !isLoading,
      login,
      logout,
      clearSession: clearAuthSession,
    }),
    [user, isError, isBootstrapped, isLoading, login, logout, clearAuthSession],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
