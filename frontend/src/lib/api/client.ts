/**
 * HTTP-клиент для API.
 *
 * - Base URL из config
 * - Bearer token из getAccessToken (подключается через setAuthTokenProvider)
 * - При 401: refresh token → retry (если настроен onRefresh)
 */

import { config } from "@/lib/config";

export type AuthTokenProvider = () => string | null;
export type RefreshTokensFn = () => Promise<{ access_token: string } | null>;

let getAccessToken: AuthTokenProvider | null = null;
let refreshTokens: RefreshTokensFn | null = null;

export function setAuthTokenProvider(provider: AuthTokenProvider): void {
  getAccessToken = provider;
}

export function setRefreshTokensFn(fn: RefreshTokensFn): void {
  refreshTokens = fn;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public body?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export interface RequestConfig extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
  skipAuth?: boolean;
}

async function buildUrl(path: string, params?: Record<string, string | number | boolean | undefined>): Promise<string> {
  if (!config.apiUrl) {
    throw new ApiError("Backend not configured (static landing mode)", 0, { code: "BACKEND_NOT_CONFIGURED" });
  }
  const base = config.apiUrl.replace(/\/$/, "");
  const url = new URL(path.startsWith("/") ? path : `/${path}`, base);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    }
  }

  return url.toString();
}

async function request<T>(
  path: string,
  options: RequestConfig = {},
  retryOn401 = true
): Promise<T> {
  const { params, skipAuth = false, ...init } = options;

  const url = await buildUrl(path, params);
  const headers = new Headers(init.headers);

  if (!skipAuth && getAccessToken) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (!headers.has("Content-Type") && init.body && typeof init.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (response.status === 401 && retryOn401 && refreshTokens) {
    const newTokens = await refreshTokens();
    if (newTokens) {
      headers.set("Authorization", `Bearer ${newTokens.access_token}`);
      const retryResponse = await fetch(url, { ...init, headers });
      if (!retryResponse.ok) {
        throw new ApiError(
          retryResponse.statusText,
          retryResponse.status,
          await safeParseJson(retryResponse)
        );
      }
      return retryResponse.json() as Promise<T>;
    }
  }

  if (!response.ok) {
    const body = await safeParseJson(response);
    throw new ApiError(
      (body as { detail?: string })?.detail ?? response.statusText,
      response.status,
      body
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

async function safeParseJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  get: <T>(path: string, config?: RequestConfig) =>
    request<T>(path, { ...config, method: "GET" }),

  post: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, { ...config, method: "POST", body: body ? JSON.stringify(body) : undefined }),

  patch: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, { ...config, method: "PATCH", body: body ? JSON.stringify(body) : undefined }),

  delete: <T>(path: string, config?: RequestConfig) =>
    request<T>(path, { ...config, method: "DELETE" }),
};
