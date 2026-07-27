"use client";

import { ProfileForm } from "@features/manage-account";
import { useAuth } from "@shared/auth";
import { Skeleton } from "@shared/ui/skeleton";

/** Client island: auth-gated profile form (token is memory-only). */
export function AccountProfilePanel() {
  const { user, isInitialized } = useAuth();

  if (!isInitialized || !user) {
    return (
      <div className="space-y-4" data-testid="profile-loading">
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-full" />
        <Skeleton className="h-12 w-2/3" />
      </div>
    );
  }

  return (
    <div className="max-w-lg">
      {/* WHY: remount after /auth/me refresh so saved server values win. */}
      <ProfileForm key={`${user.id}-${user.updated_at}`} user={user} />
    </div>
  );
}
