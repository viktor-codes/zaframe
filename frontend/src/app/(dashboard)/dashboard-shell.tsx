"use client";

import Link from "next/link";

interface DashboardShellProps {
  children: React.ReactNode;
}

export function DashboardShell({ children }: DashboardShellProps) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-6">
            <Link
              href="/"
              className="text-sm font-medium text-primary hover:text-primary-dark"
            >
              ZeeFrame
            </Link>
            <span className="text-secondary text-sm font-semibold">
              Studio dashboard
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <Link
              href="/account/bookings"
              className="text-neutral-600 hover:text-neutral-900"
            >
              My bookings
            </Link>
            <Link
              href="/studios"
              className="text-neutral-600 hover:text-neutral-900"
            >
              Explore
            </Link>
          </div>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}
