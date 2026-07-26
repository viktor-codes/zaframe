import Link from "next/link";
import { Header } from "@features/navigation/components";

export default function StudioStorefrontNotFound() {
  return (
    <>
      <Header
        minimalSearch={{
          href: "/studios",
          placeholder: "Search studios…",
        }}
      />
      <div
        className="mx-auto max-w-lg px-4 pt-36 pb-16 text-center sm:px-6"
        data-testid="studio-storefront-not-found"
      >
        <p className="font-display text-2xl font-bold text-neutral-900">
          Studio not found
        </p>
        <p className="mt-3 text-sm text-neutral-600">
          This storefront link is invalid or the studio is no longer public.
          Pick another studio from the catalog.
        </p>
        <Link
          href="/studios"
          className="mt-8 inline-flex items-center justify-center rounded-xl bg-neutral-900 px-5 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-neutral-800"
        >
          Explore studios
        </Link>
      </div>
    </>
  );
}
