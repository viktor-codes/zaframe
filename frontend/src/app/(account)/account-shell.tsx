import Link from "next/link";

import { AccountDashboardLink } from "./account-dashboard-link";
import { AccountNav } from "./account-nav";

interface AccountShellProps {
  children: React.ReactNode;
}

/**
 * Server shell: static chrome + small client islands for auth/pathname UI.
 */
export function AccountShell({ children }: AccountShellProps) {
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
            <AccountDashboardLink />
            <span className="text-secondary text-sm font-semibold">Account</span>
          </div>
        </div>
        <AccountNav />
      </header>
      <main>{children}</main>
    </div>
  );
}
