/**
 * App-wide TanStack QueryClient defaults (browser providers).
 */

import {
  MutationCache,
  QueryClient,
  type Mutation,
} from "@tanstack/react-query";

import { ApiError } from "../api/api-error";

export type AppMutationMeta = {
  /** When true, providers toast the user-facing API error. */
  toastOnError?: boolean;
};

declare module "@tanstack/react-query" {
  interface Register {
    mutationMeta: AppMutationMeta;
  }
}

function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status > 0 && error.status < 500) {
    return false;
  }
  return failureCount < 2;
}

export interface CreateAppQueryClientOptions {
  onMutationToastError?: (error: unknown) => void;
}

export function createAppQueryClient(
  options: CreateAppQueryClientOptions = {},
): QueryClient {
  return new QueryClient({
    mutationCache: new MutationCache({
      onError: (
        error,
        _variables,
        _context,
        mutation: Mutation<unknown, unknown, unknown, unknown>,
      ) => {
        if (mutation.meta?.toastOnError) {
          options.onMutationToastError?.(error);
        }
      },
    }),
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
