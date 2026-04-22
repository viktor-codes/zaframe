/**
 * Client-side storage for the short-lived access token only.
 * Refresh token is httpOnly cookie on the API origin (never localStorage).
 */

let accessToken: string | null = null;

export function getStoredAccessToken(): string | null {
  return accessToken;
}

export function getStoredRefreshToken(): string | null {
  return null;
}

export function setStoredTokens(access: string): void {
  accessToken = access;
}

export function clearStoredTokens(): void {
  accessToken = null;
}
