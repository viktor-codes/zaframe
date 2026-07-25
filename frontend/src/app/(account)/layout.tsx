import { RequireAuth } from "@shared/auth";
import { RouteErrorBoundary } from "@shared/ui";

import { AccountShell } from "./account-shell";

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteErrorBoundary
      title="Account unavailable"
      description="Your account section could not be displayed. Try again or reload the page."
    >
      <RequireAuth>
        <AccountShell>{children}</AccountShell>
      </RequireAuth>
    </RouteErrorBoundary>
  );
}
