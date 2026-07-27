/**
 * Client-side storage for the short-lived access token only.
 * Refresh token is an httpOnly cookie on the web origin (via /api rewrite; never localStorage).
 */

let accessToken: string | null = null;

export function getStoredAccessToken(): string | null {
  return accessToken;
}

export function setStoredTokens(access: string): void {
  accessToken = access;
}

export function clearStoredTokens(): void {
  accessToken = null;
}
