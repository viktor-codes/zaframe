"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { StudioSwitcher } from "@entities/studio";

interface StudioNavItem {
  label: string;
  href: string;
  /** Exact match only (Today overview). */
  isExact?: boolean;
}

function buildStudioNav(studioId: number): StudioNavItem[] {
  const base = `/dashboard/studios/${studioId}`;
  return [
    { label: "Today", href: base, isExact: true },
    { label: "Profile", href: `${base}/profile` },
    { label: "Services", href: `${base}/services` },
    { label: "Calendar", href: `${base}/calendar` },
    { label: "Bookings", href: `${base}/bookings` },
  ];
}

export interface DashboardSidebarProps {
  studios: ReadonlyArray<{ id: number; name: string }>;
  selectedStudioId: number | null;
  isStudiosLoading: boolean;
  onStudioSelect: (studioId: number) => void;
}

export function DashboardSidebar({
  studios,
  selectedStudioId,
  isStudiosLoading,
  onStudioSelect,
}: DashboardSidebarProps) {
  const pathname = usePathname();
  const studioNav =
    selectedStudioId != null ? buildStudioNav(selectedStudioId) : [];

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
            isLoading={isStudiosLoading}
            onStudioSelect={onStudioSelect}
          />
        </div>

        <nav className="space-y-1" aria-label="Dashboard">
          <SidebarLink
            href="/dashboard"
            label="My studios"
            isActive={
              pathname === "/dashboard" || pathname === "/dashboard/"
            }
          />
          {studioNav.map((item) => {
            const isActive = item.isExact
              ? pathname === item.href || pathname === `${item.href}/`
              : pathname === item.href ||
                pathname.startsWith(`${item.href}/`);

            return (
              <SidebarLink
                key={item.href}
                href={item.href}
                label={item.label}
                isActive={isActive}
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
}

function SidebarLink({ href, label, isActive }: SidebarLinkProps) {
  return (
    <Link
      href={href}
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
