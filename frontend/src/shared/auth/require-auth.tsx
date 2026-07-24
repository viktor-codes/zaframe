"use client";

/**
 * Client-side auth gate (ARCHITECTURE §3 — middleware cannot use access tokens).
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { Skeleton } from "@shared/ui";

import { useAuth } from "./context";

export interface RequireAuthProps {
  children: React.ReactNode;
  /** Default: /auth/login */
  loginHref?: string;
}

export function RequireAuth({
  children,
  loginHref = "/auth/login",
}: RequireAuthProps) {
  const { user, isInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isInitialized) return;
    if (!user) {
      router.replace(loginHref);
    }
  }, [user, isInitialized, router, loginHref]);

  if (!isInitialized || !user) {
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
