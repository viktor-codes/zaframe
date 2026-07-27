/**
 * HTTP client for the ZeeFrame API (browser / client components only).
 *
 * - Base URL from shared config
 * - Bearer token via setAuthTokenProvider
 * - On 401: single coalesced refresh → retry (unless skipAuth / skipRefresh)
 * - Sends `X-Request-ID` on every request; optional `Idempotency-Key`
 * - Forwards `AbortSignal` from RequestInit (TanStack Query `queryFn` signal)
 */

import "client-only";

import { config } from "@shared/lib/config";

import { ApiError } from "./api-error";
import { buildApiUrl, type QueryParams } from "./build-url";
import { safeParseJson, throwApiError } from "./http-error";
import {
  createRequestId,
  IDEMPOTENCY_KEY_HEADER,
  REQUEST_ID_HEADER,
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
/** In-flight refresh shared by parallel 401s (refresh-token rotation is single-use). */
let refreshInFlight: Promise<{ access_token: string } | null> | null = null;

export function setAuthTokenProvider(provider: AuthTokenProvider): void {
  getAccessToken = provider;
}

export function setRefreshTokensFn(fn: RefreshTokensFn): void {
  refreshTokens = fn;
}

export interface RequestConfig extends RequestInit {
  params?: QueryParams;
  skipAuth?: boolean;
  /**
   * Do not attempt token refresh on 401.
   * Required for `/auth/refresh` itself to avoid recursive refresh loops.
   */
  skipRefresh?: boolean;
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

async function coalesceRefresh(): Promise<{ access_token: string } | null> {
  if (!refreshTokens) {
    return null;
  }
  if (!refreshInFlight) {
    refreshInFlight = refreshTokens().finally(() => {
      refreshInFlight = null;
    });
  }
  return refreshInFlight;
}

/**
 * WHY: TanStack Query cancels via AbortSignal; after a 401 we must not start
 * refresh/retry once the caller has already abandoned the request.
 */
function throwIfAborted(signal: AbortSignal | null | undefined): void {
  if (!signal?.aborted) return;
  if (
    signal.reason instanceof DOMException &&
    signal.reason.name === "AbortError"
  ) {
    throw signal.reason;
  }
  throw new DOMException("The operation was aborted.", "AbortError");
}

async function request<T>(
  path: string,
  options: RequestConfig = {},
): Promise<T> {
  const {
    params,
    skipAuth = false,
    skipRefresh = false,
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

  // WHY: `signal` lives on RequestInit and is forwarded via `...init`.
  const response = await fetch(url, {
    ...init,
    headers,
    credentials: "include",
  });

  const canRefresh =
    response.status === 401 &&
    !skipAuth &&
    !skipRefresh &&
    refreshTokens !== null;

  if (canRefresh) {
    throwIfAborted(init.signal);
    const newTokens = await coalesceRefresh();
    throwIfAborted(init.signal);
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
        throwApiError(
          retryResponse,
          await safeParseJson(retryResponse),
          requestId,
        );
      }
      return parseSuccessBody<T>(retryResponse);
    }
  }

  if (!response.ok) {
    throwApiError(response, await safeParseJson(response), requestId);
  }

  return parseSuccessBody<T>(response);
}

async function parseSuccessBody<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
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
