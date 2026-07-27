"use client";

/**
 * Current user's studio-scoped role from GET /auth/me.
 */

import { useMemo } from "react";

import type { StudioMemberRole } from "@shared/lib/constants";

import { useAuth } from "./context";
import { resolveStudioRole } from "./resolve-studio-access";

export function useRole(
  studioId: number | null | undefined,
): StudioMemberRole | null {
  const { user } = useAuth();
  return useMemo(() => resolveStudioRole(user, studioId), [user, studioId]);
}
