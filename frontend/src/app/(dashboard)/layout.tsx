import { RequireAuth } from "@shared/auth";
import { RouteErrorBoundary } from "@shared/ui";

import { DashboardShell } from "./dashboard-shell";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteErrorBoundary
      title="Dashboard unavailable"
      description="The studio dashboard could not be displayed. Try again or reload the page."
    >
      <RequireAuth>
        <DashboardShell>{children}</DashboardShell>
      </RequireAuth>
    </RouteErrorBoundary>
  );
}
