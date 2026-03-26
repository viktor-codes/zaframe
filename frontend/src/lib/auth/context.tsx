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
import {
  api,
  setAuthTokenProvider,
  setRefreshTokensFn,
} from "@/lib/api";
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

function useAuthQuery(loginTrigger: number) {
  const hasToken =
    typeof window !== "undefined" && !!getStoredAccessToken();

  return useQuery({
    queryKey: ["auth", "me", loginTrigger],
    queryFn: () => api.get<UserResponse>("/api/v1/auth/me"),
    enabled: hasToken,
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [isInitialized, setIsInitialized] = useState(false);
  const [loginTrigger, setLoginTrigger] = useState(0);

  const { data: user, isLoading } = useAuthQuery(loginTrigger);

  const login = useCallback(
    (accessToken: string, _userData: UserResponse) => {
      setStoredTokens(accessToken);
      setAuthTokenProvider(getStoredAccessToken);
      setLoginTrigger((prev) => prev + 1);
    },
    []
  );

  const logout = useCallback(() => {
    void logoutSession().finally(() => {
      clearStoredTokens();
      setLoginTrigger((prev) => prev + 1);
    });
  }, []);

  useEffect(() => {
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
    const t = setTimeout(() => setIsInitialized(true), 0);
    return () => clearTimeout(t);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user: user ?? null,
      isInitialized: isInitialized && !isLoading,
      login,
      logout,
    }),
    [user, isInitialized, isLoading, login, logout]
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
