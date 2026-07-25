import { RouteErrorBoundary } from "@shared/ui";

/** Public zone: landing, studios, booking flow. Per-page Header where needed. */
export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <RouteErrorBoundary
      title="This page hit a snag"
      description="The public studio area failed to load. Try again, or head back to studios."
    >
      <div className="min-h-screen bg-neutral-50">
        <main className="min-h-[calc(100vh-130px)]">{children}</main>
      </div>
    </RouteErrorBoundary>
  );
}
