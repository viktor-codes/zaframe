"use client";

import Link from "next/link";
import { useMemo } from "react";

import { usePermission } from "@shared/auth";
import {
  buildStudioDashboardNav,
  filterStudioDashboardNav,
} from "@shared/lib";

export interface TodayQuickActionsProps {
  studioId: number;
}

export function TodayQuickActions({ studioId }: TodayQuickActionsProps) {
  const { can } = usePermission(studioId);

  const actions = useMemo(
    () =>
      filterStudioDashboardNav(buildStudioDashboardNav(studioId), can).filter(
        (item) => item.id !== "today",
      ),
    [can, studioId],
  );

  if (actions.length === 0) {
    return null;
  }

  return (
    <nav aria-label="Quick actions" data-testid="today-quick-actions">
      <p className="mb-2 text-xs font-semibold tracking-wide text-neutral-500 uppercase">
        Quick actions
      </p>
      <ul className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <li key={action.href}>
            <Link
              href={action.href}
              data-testid={`today-action-${action.id}`}
              className="inline-flex rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-800 hover:border-neutral-300 hover:bg-neutral-50"
            >
              {action.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
