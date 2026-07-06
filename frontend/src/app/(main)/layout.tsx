/** Public zone: landing, studios, booking flow. Per-page Header where needed. */
export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <main className="min-h-[calc(100vh-130px)]">{children}</main>
    </div>
  );
}
