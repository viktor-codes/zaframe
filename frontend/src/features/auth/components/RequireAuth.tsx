"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Skeleton } from "@/components/ui";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isInitialized } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isInitialized) return;
    if (!user) {
      router.replace("/auth/login");
    }
  }, [user, isInitialized, router]);

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
