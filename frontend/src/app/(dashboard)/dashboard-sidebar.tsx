"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo } from "react";

import { StudioSwitcher, useMyStudios } from "@entities/studio";
import { usePermission } from "@shared/auth";
import {
  buildStudioDashboardNav,
  filterStudioDashboardNav,
} from "@shared/lib/studio-dashboard-nav";

import { parseDashboardStudioId } from "./parse-dashboard-studio-id";

/**
 * Client island: studio list + permission-filtered nav.
 * Shell chrome stays on the server around this leaf.
 */
export function DashboardSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const selectedStudioId = parseDashboardStudioId(pathname);
  const { data, isLoading } = useMyStudios();
  const studios = data?.items ?? [];
  const { can } = usePermission(selectedStudioId);

  const studioNav = useMemo(() => {
    if (selectedStudioId == null) return [];
    return filterStudioDashboardNav(
      buildStudioDashboardNav(selectedStudioId),
      can,
    );
  }, [can, selectedStudioId]);

  return (
    <aside
      className="border-b border-neutral-200 bg-white lg:flex lg:w-64 lg:shrink-0 lg:flex-col lg:border-r lg:border-b-0"
      data-testid="dashboard-sidebar"
    >
      <div className="space-y-4 px-4 py-4 lg:flex-1 lg:px-5 lg:py-6">
        <div>
          <p className="mb-2 text-xs font-semibold tracking-wide text-neutral-500 uppercase">
            Studio
          </p>
          <StudioSwitcher
            studios={studios}
            selectedStudioId={selectedStudioId}
            isLoading={isLoading}
            onStudioSelect={(studioId) => {
              router.push(`/dashboard/studios/${studioId}`);
            }}
          />
        </div>

        <nav className="space-y-1" aria-label="Dashboard">
          <SidebarLink
            href="/dashboard"
            label="My studios"
            isActive={pathname === "/dashboard" || pathname === "/dashboard/"}
          />
          {studioNav.map((item) => {
            const isActive = item.isExact
              ? pathname === item.href || pathname === `${item.href}/`
              : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <SidebarLink
                key={item.href}
                href={item.href}
                label={item.label}
                isActive={isActive}
                testId={`dashboard-nav-${item.id}`}
              />
            );
          })}
        </nav>
      </div>

      <div className="hidden border-t border-neutral-200 px-5 py-4 lg:block">
        <Link
          href="/dashboard/studios/new"
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          + Create studio
        </Link>
      </div>
    </aside>
  );
}

interface SidebarLinkProps {
  href: string;
  label: string;
  isActive: boolean;
  testId?: string;
}

function SidebarLink({ href, label, isActive, testId }: SidebarLinkProps) {
  return (
    <Link
      href={href}
      data-testid={testId}
      className={`block rounded-lg px-3 py-2 text-sm font-medium ${
        isActive
          ? "bg-teal-50 text-teal-900"
          : "text-neutral-700 hover:bg-neutral-50 hover:text-neutral-900"
      }`}
      aria-current={isActive ? "page" : undefined}
    >
      {label}
    </Link>
  );
}
