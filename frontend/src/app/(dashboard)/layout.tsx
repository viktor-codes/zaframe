import { RequireAuth } from "@shared/auth";
import { RouteErrorBoundary } from "@shared/ui/route-error-boundary";

import { DashboardShell } from "./dashboard-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RequireAuth>
      <DashboardShell>
        <RouteErrorBoundary
          title="Dashboard unavailable"
          description="The studio dashboard could not be displayed. Try again or reload the page."
        >
          {children}
        </RouteErrorBoundary>
      </DashboardShell>
    </RequireAuth>
  );
}
