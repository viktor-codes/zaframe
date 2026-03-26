/**
 * Map API failures to short, user-safe copy (RFC 7807 / FastAPI detail).
 * Do not surface raw stack traces or internal keys to end users.
 */

import { ApiError } from "./client";

type ValidationIssue = {
  loc?: (string | number)[];
  msg?: string;
  type?: string;
};

type ProblemLike = {
  detail?: string | ValidationIssue[] | Record<string, unknown>;
  title?: string;
};

/**
 * Returns a single line suitable for alerts and inline form errors.
 */
export function getUserFacingApiMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const fromBody = formatProblemDetail(error.body);
    if (fromBody) return fromBody;
    if (error.message && !isTechnicalNoise(error.message)) {
      return error.message;
    }
    return defaultMessageForStatus(error.status);
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Something went wrong. Please try again.";
}

function isTechnicalNoise(message: string): boolean {
  return message === "Failed to fetch" || message.startsWith("NetworkError");
}

function defaultMessageForStatus(status: number): string {
  if (status === 0)
    return "Network error. Check your connection and try again.";
  if (status === 401) return "Please sign in to continue.";
  if (status === 403) return "You do not have permission to do that.";
  if (status === 404) return "The requested resource was not found.";
  if (status === 409)
    return "This action could not be completed. Please refresh and try again.";
  if (status === 422) return "Please check the form and try again.";
  if (status >= 500)
    return "Something went wrong on our side. Please try again later.";
  return "Request failed. Please try again.";
}

function formatProblemDetail(body: unknown): string {
  if (body === null || body === undefined) return "";
  if (typeof body === "string") return body;
  if (typeof body !== "object") return "";

  const problem = body as ProblemLike;
  const detail = problem.detail;

  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as ValidationIssue).msg ?? "");
        }
        return "";
      })
      .filter(Boolean);
    if (parts.length > 0) return parts.join(" ");
  }

  if (typeof problem.title === "string" && problem.title) {
    return problem.title;
  }

  return "";
}
