export default function MainLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-neutral-50">
      {/* <Header /> */}
      <main className="min-h-[calc(100vh-130px)]">{children}</main>
    </div>
  );
}
