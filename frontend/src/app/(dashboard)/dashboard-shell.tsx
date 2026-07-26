"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

import { useMyStudios } from "@entities/studio";

import { DashboardSidebar } from "./dashboard-sidebar";
import { parseDashboardStudioId } from "./parse-dashboard-studio-id";

interface DashboardShellProps {
  children: React.ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const selectedStudioId = parseDashboardStudioId(pathname);
  const { data, isLoading } = useMyStudios();
  const studios = data?.items ?? [];

  return (
    <div className="min-h-screen bg-neutral-50 lg:flex">
      <DashboardSidebar
        studios={studios}
        selectedStudioId={selectedStudioId}
        isStudiosLoading={isLoading}
        onStudioSelect={(studioId) => {
          router.push(`/dashboard/studios/${studioId}`);
        }}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-neutral-200 bg-white">
          <div className="flex items-center justify-between gap-4 px-4 py-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-4">
              <Link
                href="/"
                className="shrink-0 text-sm font-medium text-primary hover:text-primary-dark"
              >
                ZeeFrame
              </Link>
              <span className="text-secondary truncate text-sm font-semibold">
                Studio dashboard
              </span>
            </div>
            <div className="flex shrink-0 items-center gap-4 text-sm">
              <Link
                href="/account/bookings"
                className="text-neutral-600 hover:text-neutral-900"
                data-testid="dashboard-account-link"
              >
                Account
              </Link>
              <Link
                href="/studios"
                className="hidden text-neutral-600 hover:text-neutral-900 sm:inline"
              >
                Explore
              </Link>
            </div>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
