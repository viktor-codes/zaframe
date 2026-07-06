/**
 * Magic-link auth API (login flow).
 *
 * Session refresh/logout live in `@shared/auth/api`.
 */
import { api } from "@shared/api";
import type { components } from "@shared/api";

type MagicLinkVerifyResponse = components["schemas"]["TokenResponse"] & {
  user: components["schemas"]["UserResponse"];
};

export async function requestMagicLink(params: {
  email: string;
  name: string;
}): Promise<void> {
  await api.post<{ message?: string }>(
    "api/v1/auth/magic-link/request",
    params,
    { skipAuth: true },
  );
}

export async function verifyMagicLink(
  token: string,
): Promise<MagicLinkVerifyResponse> {
  return api.get<MagicLinkVerifyResponse>("api/v1/auth/magic-link/verify", {
    params: { token },
    skipAuth: true,
  });
}
