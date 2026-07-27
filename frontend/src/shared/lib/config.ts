/**
 * Application configuration from environment variables.
 *
 * Client-side Next.js code must read process.env.NEXT_PUBLIC_* statically —
 * dynamic keys are not inlined into the browser bundle.
 *
 * Auth cookie topology (ARCHITECTURE §3):
 * - Browser calls NEXT_PUBLIC_API_URL (same origin as the Next app).
 * - Next rewrites /api/* → API_UPSTREAM_URL (real FastAPI).
 * - Set-Cookie lands on the web origin so CSRF double-submit can read csrf_token.
 */

export interface ApiUrlConfig {
  /** Browser-facing API base (usually the Next origin). */
  apiUrl: string;
  /** Server-side FastAPI base for RSC and next.config rewrites. */
  apiUpstreamUrl: string;
  /** True when the browser-facing API URL is configured. */
  hasBackend: boolean;
}

function trimBaseUrl(value: string | undefined): string {
  return (value ?? "").trim().replace(/\/$/, "");
}

/**
 * Resolve public vs upstream API bases from env-shaped input.
 * Pure helper — unit-tested; `config` below binds process.env at module load.
 */
export function resolveApiUrls(env: {
  NEXT_PUBLIC_API_URL?: string;
  API_UPSTREAM_URL?: string;
}): ApiUrlConfig {
  const apiUrl = trimBaseUrl(env.NEXT_PUBLIC_API_URL);
  const upstream = trimBaseUrl(env.API_UPSTREAM_URL);
  // WHY: RSC can fall back to the public URL in single-origin local setups.
  const apiUpstreamUrl = upstream || apiUrl;
  return {
    apiUrl,
    apiUpstreamUrl,
    hasBackend: apiUrl.length > 0,
  };
}

export const config: ApiUrlConfig = resolveApiUrls({
  NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  API_UPSTREAM_URL: process.env.API_UPSTREAM_URL,
});
