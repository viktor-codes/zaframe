"use client";

/**
 * Require membership (and optional role allow-list) for a studio.
 * Must sit inside RequireAuth (or after it) — unauthenticated users redirect to login.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import type { StudioMemberRole } from "@shared/lib/constants";
import { Skeleton } from "@shared/ui";

import { useAuth } from "./context";
import { hasStudioRole } from "./resolve-studio-access";

export interface RequireStudioRoleProps {
  studioId: number;
  /** If omitted, any studio membership is enough. */
  roles?: readonly StudioMemberRole[];
  children: React.ReactNode;
  /** Default: /dashboard */
  fallbackHref?: string;
  loginHref?: string;
}

export function RequireStudioRole({
  studioId,
  roles,
  children,
  fallbackHref = "/dashboard",
  loginHref = "/auth/login",
}: RequireStudioRoleProps) {
  const { user, isInitialized } = useAuth();
  const router = useRouter();
  const isAllowed = hasStudioRole(user, studioId, roles);

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
