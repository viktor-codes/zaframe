/**
 * Unauthenticated API fetch for React Server Components (public endpoints only).
 *
 * WHY: access tokens live in client memory; the Next.js server cannot authenticate.
 * Import from `@shared/api/server` — never from the `@shared/api` barrel (that pulls
 * `client-only` code and breaks RSC).
 */

import "server-only";

import type { StudioPublicResponse } from "@entities/studio";
import { config } from "@shared/lib/config";

import { ApiError } from "./api-error";
import { buildApiUrl, type QueryParams } from "./build-url";
import { safeParseJson, throwApiError } from "./http-error";
import { createRequestId, REQUEST_ID_HEADER } from "./request-headers";

/** Default ISR window for storefront data (ARCHITECTURE §3). */
export const STOREFRONT_REVALIDATE_SECONDS = 60;

export interface ServerRequestConfig {
  params?: QueryParams;
  /** Override auto-generated `X-Request-ID`. */
  requestId?: string;
  /** Next.js fetch cache options (`revalidate`, `tags`). */
  next?: {
    revalidate?: number | false;
    tags?: string[];
  };
  cache?: RequestCache;
}

function resolveServerUrl(
  path: string,
  params?: ServerRequestConfig["params"],
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

/**
 * GET a public API path from a Server Component (no cookies, no Bearer).
 */
export async function serverGet<T>(
  path: string,
  options: ServerRequestConfig = {},
): Promise<T> {
  const { params, requestId: requestIdOption, next, cache } = options;
  const requestId = requestIdOption ?? createRequestId();
  const url = resolveServerUrl(path, params);

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      [REQUEST_ID_HEADER]: requestId,
    },
    ...(next !== undefined ? { next } : {}),
    ...(cache !== undefined ? { cache } : {}),
  });

  if (!response.ok) {
    throwApiError(response, await safeParseJson(response), requestId);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

/**
 * Public storefront payload for `/s/[slug]` (ISR default: 60s).
 */
export async function fetchStudioPublicBySlug(
  slug: string,
  options: Omit<ServerRequestConfig, "params"> = {},
): Promise<StudioPublicResponse> {
  const encoded = encodeURIComponent(slug);
  return serverGet<StudioPublicResponse>(
    `api/v1/studios/slug/${encoded}/public`,
    {
      ...options,
      next: {
        revalidate: STOREFRONT_REVALIDATE_SECONDS,
        ...options.next,
      },
    },
  );
}
