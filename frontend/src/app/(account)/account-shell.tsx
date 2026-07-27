import Link from "next/link";

import { LegalLinks } from "@shared/ui/legal-links";

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
    <div className="flex min-h-screen flex-col bg-neutral-50">
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
      <main className="flex-1">{children}</main>
      <footer className="border-t border-neutral-200 bg-white px-6 py-4">
        <div className="mx-auto flex max-w-4xl justify-end">
          <LegalLinks />
        </div>
      </footer>
    </div>
  );
}
