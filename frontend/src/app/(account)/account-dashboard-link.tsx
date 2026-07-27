"use client";

import Link from "next/link";

import { useAuth } from "@shared/auth";

/** Shows Studio dashboard cross-link when the user has any studio role. */
export function AccountDashboardLink() {
  const { user } = useAuth();
  const hasStudioRole = (user?.roles?.length ?? 0) > 0;

  if (!hasStudioRole) return null;

  return (
    <Link
      href="/dashboard"
      className="text-sm text-neutral-600 hover:text-neutral-900"
      data-testid="account-dashboard-link"
    >
      Studio dashboard
    </Link>
  );
}
