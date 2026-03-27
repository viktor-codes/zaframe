/**
 * Pure URL builder for API requests (testable without fetch / config singleton).
 */

export type QueryParamValue =
  | string
  | number
  | boolean
  | undefined
  | (string | number)[];

export type QueryParams = Record<string, QueryParamValue>;

/**
 * Build an absolute API URL from a trimmed base and path, with optional query params.
 *
 * @param apiBaseUrl - Base origin (e.g. https://api.example.com), no trailing slash required
 * @param path - Path beginning with / or relative segment
 * @param params - Query parameters (arrays are repeated keys)
 */
export function buildApiUrl(
  apiBaseUrl: string,
  path: string,
  params?: QueryParams,
): string {
  const base = apiBaseUrl.replace(/\/$/, "");
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = new URL(normalizedPath, `${base}/`);

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined) continue;
      if (Array.isArray(value)) {
        for (const v of value) {
          url.searchParams.append(key, String(v));
        }
      } else {
        url.searchParams.set(key, String(value));
      }
    }
  }

  return url.toString();
}
