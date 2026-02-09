/**
 * Типы аутентификации по backend schemas.
 */

import type { UserResponse } from "./user";

export interface MagicLinkRequest {
  email: string;
  name: string;
}

export interface MagicLinkSentResponse {
  message: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface MagicLinkVerifyResponse extends TokenResponse {
  user: UserResponse;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}
