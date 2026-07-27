"use client";

/**
 * Permission checks for a studio — UX-only; API still enforces access.
 */

import { useCallback, useMemo } from "react";

import type { StudioMemberRole, StudioPermission } from "@shared/lib/constants";
import { roleHasPermission } from "@shared/lib/constants";

import { useRole } from "./use-role";

export interface UsePermissionResult {
  role: StudioMemberRole | null;
  can: (permission: StudioPermission) => boolean;
}

export function usePermission(
  studioId: number | null | undefined,
): UsePermissionResult {
  const role = useRole(studioId);

  const can = useCallback(
    (permission: StudioPermission) => roleHasPermission(role, permission),
    [role],
  );

  return useMemo(() => ({ role, can }), [role, can]);
}
