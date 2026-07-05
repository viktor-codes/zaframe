/**
 * Application configuration from environment variables.
 *
 * Client-side Next.js code must read process.env.NEXT_PUBLIC_* statically —
 * dynamic keys are not inlined into the browser bundle.
 */

const rawApiUrl = process.env.NEXT_PUBLIC_API_URL ?? "";
const apiUrl = rawApiUrl.trim();

export const config = {
  /** API base URL (trimmed). Empty means misconfiguration — the app needs a backend. */
  apiUrl,
  /** True when NEXT_PUBLIC_API_URL is set — API calls are possible. */
  hasBackend: apiUrl.length > 0,
} as const;
