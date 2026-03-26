/**
 * API аутентификации: Magic Link.
 */
import { api } from "./client";
import type {
  MagicLinkVerifyResponse,
  RefreshTokenResponse,
} from "@/types/auth";

export async function requestMagicLink(params: {
  email: string;
  name: string;
}): Promise<void> {
  await api.post<{ message?: string }>(
    "api/v1/auth/magic-link/request",
    params,
    { skipAuth: true },
  );
}

export async function verifyMagicLink(
  token: string,
): Promise<MagicLinkVerifyResponse> {
  return api.get<MagicLinkVerifyResponse>(`api/v1/auth/magic-link/verify`, {
    params: { token },
    skipAuth: true,
  });
}

export async function refreshAccessToken(): Promise<RefreshTokenResponse> {
  return api.post<RefreshTokenResponse>("/api/v1/auth/refresh", undefined, {
    skipAuth: true,
  });
}

export async function logoutSession(): Promise<void> {
  await api.post<void>("/api/v1/auth/logout", undefined, { skipAuth: false });
}
