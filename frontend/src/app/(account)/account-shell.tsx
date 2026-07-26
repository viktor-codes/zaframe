"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@shared/auth";

const NAV_ITEMS = [
  { href: "/account/bookings", label: "My bookings" },
  { href: "/account/orders", label: "Orders" },
  { href: "/account/profile", label: "Profile" },
] as const;

interface AccountShellProps {
  children: React.ReactNode;
}

export function AccountShell({ children }: AccountShellProps) {
  const pathname = usePathname();
  const { user } = useAuth();
  const hasStudioRole = (user?.roles?.length ?? 0) > 0;

  return (
    <div className="min-h-screen bg-neutral-50">
      <header className="border-b border-neutral-200 bg-white">
        <div className="mx-auto flex max-w-4xl items-center justify-between gap-4 px-6 py-4">
          <Link
            href="/"
            className="text-sm font-medium text-primary hover:text-primary-dark"
          >
            ← ZeeFrame
          </Link>
          <div className="flex items-center gap-4">
            {hasStudioRole ? (
              <Link
                href="/dashboard"
                className="text-sm text-neutral-600 hover:text-neutral-900"
                data-testid="account-dashboard-link"
              >
                Studio dashboard
              </Link>
            ) : null}
            <span className="text-secondary text-sm font-semibold">Account</span>
          </div>
        </div>
        <nav
          className="mx-auto flex max-w-4xl gap-6 px-6 pb-3"
          aria-label="Account"
        >
          {NAV_ITEMS.map((item) => {
            const isActive =
              pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`text-sm font-medium ${
                  isActive
                    ? "text-primary"
                    : "text-neutral-600 hover:text-neutral-900"
                }`}
                aria-current={isActive ? "page" : undefined}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
