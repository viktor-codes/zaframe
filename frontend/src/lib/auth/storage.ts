/**
 * Client-side storage for the short-lived access token only.
 * Refresh token is httpOnly cookie on the API origin (never localStorage).
 */

const ACCESS_KEY = "zaframe_access_token";

export function getStoredAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getStoredRefreshToken(): string | null {
  return null;
}

export function setStoredTokens(access: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_KEY, access);
}

export function clearStoredTokens(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_KEY);
}
