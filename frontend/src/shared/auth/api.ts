import "client-only";

import { api } from "@shared/api";
import type { components } from "@shared/api";

type TokenResponse = components["schemas"]["TokenResponse"];

function getCookieValue(name: string): string | null {
  if (typeof document === "undefined") return null;
  const parts = document.cookie.split(";").map((p) => p.trim());
  for (const p of parts) {
    if (!p.startsWith(`${name}=`)) continue;
    return decodeURIComponent(p.slice(name.length + 1));
  }
  return null;
}

export async function refreshAccessToken(): Promise<TokenResponse> {
  const csrf = getCookieValue("csrf_token");
  return api.post<TokenResponse>("/api/v1/auth/refresh", undefined, {
    skipAuth: true,
    headers: csrf ? { "X-CSRF-Token": csrf } : undefined,
  });
}

export async function logoutSession(): Promise<void> {
  await api.post<void>("/api/v1/auth/logout", undefined, { skipAuth: false });
}
