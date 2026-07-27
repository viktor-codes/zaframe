import { RouteErrorBoundary } from "@shared/ui";
import { LegalLinks } from "@shared/ui/legal-links";

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
      <div className="flex min-h-screen flex-col bg-neutral-50">
        <main className="min-h-[calc(100vh-130px)] flex-1">{children}</main>
        <footer className="border-t border-neutral-200 bg-white px-6 py-4">
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-4">
            <span className="text-xs text-neutral-400">ZeeFrame</span>
            <LegalLinks />
          </div>
        </footer>
      </div>
    </RouteErrorBoundary>
  );
}
