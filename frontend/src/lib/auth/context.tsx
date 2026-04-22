"use client";

/**
 * Auth контекст и провайдер.
 *
 * - Инициализирует API client с getAccessToken и refreshTokens
 * - Предоставляет user, login, logout
 * - User загружается через TanStack Query при наличии токена
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useQuery } from "@tanstack/react-query";
import { api, setAuthTokenProvider, setRefreshTokensFn } from "@/lib/api";
import {
  clearStoredTokens,
  getStoredAccessToken,
  setStoredTokens,
} from "./storage";
import type { AuthActions, AuthState } from "./types";
import type { UserResponse } from "@/types";
import { logoutSession, refreshAccessToken } from "@/lib/api/auth";

type AuthContextValue = AuthState & AuthActions;

const AuthContext = createContext<AuthContextValue | null>(null);

function useAuthQuery(loginTrigger: number, isReady: boolean) {
  return useQuery({
    queryKey: ["auth", "me", loginTrigger],
    queryFn: () => api.get<UserResponse>("/api/v1/auth/me"),
    enabled: isReady,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isBootstrapped, setIsBootstrapped] = useState(false);
  const [loginTrigger, setLoginTrigger] = useState(0);

  const { data: user, isLoading } = useAuthQuery(loginTrigger, isBootstrapped);

  const login = useCallback((accessToken: string, _userData: UserResponse) => {
    setStoredTokens(accessToken);
    setAuthTokenProvider(getStoredAccessToken);
    setLoginTrigger((prev) => prev + 1);
    setIsBootstrapped(true);
  }, []);

  const logout = useCallback(() => {
    void logoutSession().finally(() => {
      clearStoredTokens();
      setLoginTrigger((prev) => prev + 1);
      setIsBootstrapped(true);
    });
  }, []);

  useEffect(() => {
    // Migration: remove legacy token left from previous implementation.
    // Access token is memory-only now.
    try {
      if (typeof window !== "undefined") {
        window.localStorage.removeItem("zaframe_access_token");
      }
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

    setTimeout(() => setIsBootstrapped(true), 0);
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
