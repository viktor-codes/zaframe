"use client";

import { ProfileForm } from "@features/manage-account";
import { useAuth } from "@shared/auth";
import { Skeleton } from "@shared/ui";

export default function AccountProfilePage() {
  const { user, isInitialized } = useAuth();

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        Profile
      </h1>
      <p className="mb-8 text-neutral-600">
        Keep your name and contact details up to date for bookings.
      </p>

      {!isInitialized || !user ? (
        <div className="space-y-4" data-testid="profile-loading">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-12 w-2/3" />
        </div>
      ) : (
        <div className="max-w-lg">
          {/* WHY: remount after /auth/me refresh so saved server values win. */}
          <ProfileForm key={`${user.id}-${user.updated_at}`} user={user} />
        </div>
      )}
    </div>
  );
}
