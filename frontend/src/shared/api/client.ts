/**
 * HTTP client for the ZeeFrame API (browser / client components only).
 *
 * - Base URL from shared config
 * - Bearer token via setAuthTokenProvider
 * - On 401: refresh token → retry when setRefreshTokensFn is configured
 * - Sends `X-Request-ID` on every request; optional `Idempotency-Key`
 */

import "client-only";

import { config } from "@shared/lib/config";

import { ApiError } from "./api-error";
import { buildApiUrl, type QueryParams } from "./build-url";
import {
  createRequestId,
  IDEMPOTENCY_KEY_HEADER,
  REQUEST_ID_HEADER,
  resolveRequestIdFromResponse,
} from "./request-headers";

export { ApiError };
export {
  createIdempotencyKey,
  createRequestId,
  IDEMPOTENCY_KEY_HEADER,
  REQUEST_ID_HEADER,
} from "./request-headers";

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

export interface RequestConfig extends RequestInit {
  params?: QueryParams;
  skipAuth?: boolean;
  /** Override auto-generated `X-Request-ID` (e.g. reuse across a 401 retry). */
  requestId?: string;
  /** When set, sent as `Idempotency-Key` (checkout / create booking). */
  idempotencyKey?: string;
}

function resolveRequestUrl(
  path: string,
  params?: RequestConfig["params"],
): string {
  if (!config.apiUrl) {
    throw new ApiError(
      "Backend URL is not configured (set NEXT_PUBLIC_API_URL)",
      0,
      {
        code: "BACKEND_NOT_CONFIGURED",
      },
    );
  }
  return buildApiUrl(config.apiUrl, path, params);
}

function applyClientHeaders(
  headers: Headers,
  options: {
    skipAuth: boolean;
    requestId: string;
    idempotencyKey?: string;
    body?: BodyInit | null;
  },
): void {
  if (!headers.has(REQUEST_ID_HEADER)) {
    headers.set(REQUEST_ID_HEADER, options.requestId);
  }

  if (options.idempotencyKey && !headers.has(IDEMPOTENCY_KEY_HEADER)) {
    headers.set(IDEMPOTENCY_KEY_HEADER, options.idempotencyKey);
  }

  if (!options.skipAuth && getAccessToken) {
    const token = getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  if (
    !headers.has("Content-Type") &&
    options.body &&
    typeof options.body === "string"
  ) {
    headers.set("Content-Type", "application/json");
  }
}

function throwApiError(response: Response, body: unknown): never {
  const requestId = resolveRequestIdFromResponse(response, body);
  const detail =
    body && typeof body === "object" && "detail" in body
      ? (body as { detail?: unknown }).detail
      : undefined;
  const message =
    typeof detail === "string" && detail.trim()
      ? detail
      : response.statusText || "Request failed";

  throw new ApiError(message, response.status, body, requestId);
}

async function request<T>(
  path: string,
  options: RequestConfig = {},
  retryOn401 = true,
): Promise<T> {
  const {
    params,
    skipAuth = false,
    requestId: requestIdOption,
    idempotencyKey,
    ...init
  } = options;

  const requestId = requestIdOption ?? createRequestId();
  const url = resolveRequestUrl(path, params);
  const headers = new Headers(init.headers);

  applyClientHeaders(headers, {
    skipAuth,
    requestId,
    idempotencyKey,
    body: init.body,
  });

  const response = await fetch(url, {
    ...init,
    headers,
    credentials: "include",
  });

  if (response.status === 401 && retryOn401 && refreshTokens) {
    const newTokens = await refreshTokens();
    if (newTokens) {
      headers.set("Authorization", `Bearer ${newTokens.access_token}`);
      // WHY: same request id on retry keeps logs correlatable across refresh.
      headers.set(REQUEST_ID_HEADER, requestId);
      const retryResponse = await fetch(url, {
        ...init,
        headers,
        credentials: "include",
      });
      if (!retryResponse.ok) {
        throwApiError(retryResponse, await safeParseJson(retryResponse));
      }
      return parseSuccessBody<T>(retryResponse);
    }
  }

  if (!response.ok) {
    throwApiError(response, await safeParseJson(response));
  }

  return parseSuccessBody<T>(response);
}

async function parseSuccessBody<T>(response: Response): Promise<T> {
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
    request<T>(path, {
      ...config,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(path: string, body?: unknown, config?: RequestConfig) =>
    request<T>(path, {
      ...config,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(path: string, config?: RequestConfig) =>
    request<T>(path, { ...config, method: "DELETE" }),
};
