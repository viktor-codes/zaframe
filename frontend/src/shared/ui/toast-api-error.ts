"use client";

/**
 * Show a user-safe toast for an API / unknown failure.
 */

import { ApiError } from "@shared/api/api-error";
import { getUserFacingApiMessage } from "@shared/api/error-message";

import { toast } from "./toast-store";

export function toastApiError(error: unknown): string {
  const requestId = error instanceof ApiError ? error.requestId : undefined;
  return toast.error(getUserFacingApiMessage(error), { requestId });
}
