"use client";

/**
 * Require a studio permission for a route (ARCHITECTURE permission model).
 * Prefer this over role allow-lists so nav, CTAs, and pages share one matrix.
 * Must sit inside RequireAuth — unauthenticated users redirect to login.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import type { StudioPermission } from "@shared/lib/constants";
import { Skeleton } from "@shared/ui";

import { useAuth } from "./context";
import { canStudioPermission } from "./resolve-studio-access";

export interface RequireStudioPermissionProps {
  studioId: number;
  permission: StudioPermission;
  children: React.ReactNode;
  /** Default: /dashboard */
  fallbackHref?: string;
  loginHref?: string;
}

export function RequireStudioPermission({
  studioId,
  permission,
  children,
  fallbackHref = "/dashboard",
  loginHref = "/auth/login",
}: RequireStudioPermissionProps) {
  const { user, isInitialized } = useAuth();
  const router = useRouter();
  const isAllowed = canStudioPermission(user, studioId, permission);

  useEffect(() => {
    if (!isInitialized) return;
    if (!user) {
      router.replace(loginHref);
      return;
    }
    if (!isAllowed) {
      router.replace(fallbackHref);
    }
  }, [isInitialized, user, isAllowed, router, loginHref, fallbackHref]);

  if (!isInitialized || !user || !isAllowed) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <div className="text-center">
          <Skeleton className="mx-auto mb-4 h-12 w-48" />
          <Skeleton className="mx-auto h-4 w-64" />
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
