import { RequireAuth } from "@shared/auth";
import { RouteErrorBoundary } from "@shared/ui";

import { AccountShell } from "./account-shell";

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <AccountShell>
        <RouteErrorBoundary
          title="Account unavailable"
          description="Your account section could not be displayed. Try again or reload the page."
        >
          {children}
        </RouteErrorBoundary>
      </AccountShell>
    </RequireAuth>
  );
}
