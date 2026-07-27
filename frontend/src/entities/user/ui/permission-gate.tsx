"use client";

/**
 * Conditionally render UI when the current user has a studio permission.
 * UX-only — the API still enforces access server-side.
 */

import type { StudioPermission } from "@shared/lib/constants";
import { usePermission } from "@shared/auth";

export interface PermissionGateProps {
  studioId: number;
  permission: StudioPermission;
  children: React.ReactNode;
  /** Rendered when the user lacks the permission. Default: nothing. */
  fallback?: React.ReactNode;
}

export function PermissionGate({
  studioId,
  permission,
  children,
  fallback = null,
}: PermissionGateProps) {
  const { can } = usePermission(studioId);

  if (!can(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
