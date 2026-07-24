"use client";

/**
 * Auth context and provider.
 *
 * - Wires API client with getAccessToken and refreshTokens
 * - Exposes user, login, logout
 * - User is loaded via TanStack Query when a token is present
 */

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { api, setAuthTokenProvider, setRefreshTokensFn } from "@shared/api";
import { queryKeys } from "@shared/lib/query-keys";
import { logoutSession, refreshAccessToken } from "./api";
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
      return null;
    }
  });
}

function useAuthQuery(loginTrigger: number, isReady: boolean) {
  return useQuery({
    queryKey: queryKeys.auth.me(loginTrigger),
    queryFn: () => api.get<AuthUser>("/api/v1/auth/me"),
    enabled: isReady,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loginTrigger, setLoginTrigger] = useState(0);
  const [isBootstrapped] = useState(() => {
    if (typeof window === "undefined") {
      return false;
    }
    bootstrapAuthClient();
    return true;
  });

  const { data: user, isLoading } = useAuthQuery(loginTrigger, isBootstrapped);

  const login = useCallback((accessToken: string) => {
    setStoredTokens(accessToken);
    setAuthTokenProvider(getStoredAccessToken);
    setLoginTrigger((prev) => prev + 1);
  }, []);

  const logout = useCallback(() => {
    void logoutSession().finally(() => {
      clearStoredTokens();
      setLoginTrigger((prev) => prev + 1);
    });
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: user ?? null,
      isInitialized: isBootstrapped && !isLoading,
      login,
      logout,
    }),
    [user, isBootstrapped, isLoading, login, logout],
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
