/**
 * App-wide TanStack QueryClient defaults (browser providers).
 */

import { QueryClient } from "@tanstack/react-query";

import { ApiError } from "../api/api-error";

function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status > 0 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export function createAppQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        retry: shouldRetryQuery,
      },
      mutations: {
        retry: false,
      },
    },
  });
}
