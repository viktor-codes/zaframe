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
  token_type: string;
}

export interface MagicLinkVerifyResponse extends TokenResponse {
  user: UserResponse;
}

export type RefreshTokenResponse = TokenResponse;
