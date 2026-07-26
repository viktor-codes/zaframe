import Link from "next/link";

export function EmptyServicesState() {
  return (
    <div
      className="rounded-2xl border border-dashed border-neutral-200 bg-white px-6 py-12 text-center"
      data-testid="studio-storefront-empty"
    >
      <p className="font-display text-lg font-semibold text-neutral-900">
        No classes on the board yet
      </p>
      <p className="mx-auto mt-2 max-w-md text-sm text-neutral-600">
        This studio hasn&apos;t published sessions. Browse other studios while
        they set the schedule.
      </p>
      <Link
        href="/studios"
        className="mt-6 inline-flex items-center justify-center rounded-xl bg-neutral-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-neutral-800"
      >
        Explore studios
      </Link>
    </div>
  );
}
