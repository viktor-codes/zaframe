import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Cookies | ZeeFrame",
  description: "How ZeeFrame uses cookies for sign-in and security.",
};

export default function CookiesPage() {
  return (
    <article
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="cookies-page"
    >
      <p className="mb-6">
        <Link
          href="/"
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← ZeeFrame
        </Link>
      </p>
      <h1 className="text-secondary mb-4 font-display text-3xl font-bold">
        Cookies notice
      </h1>
      <p className="mb-6 text-sm text-neutral-600">
        Short notice for closed beta. Last updated 27 Jul 2026.
      </p>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">
          Essential cookies
        </h2>
        <p>
          We use httpOnly cookies for the refresh session and a readable CSRF
          token so signed-in actions stay same-site and safe. These are required
          for login to work — not advertising cookies.
        </p>
      </section>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">Analytics</h2>
        <p>
          No third-party advertising cookies in this beta. If error monitoring
          (for example Sentry) is enabled, it may use first-party technical
          storage only as needed to report failures.
        </p>
      </section>

      <section className="space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">More</h2>
        <p>
          See the{" "}
          <Link href="/privacy" className="text-primary underline">
            Privacy notice
          </Link>{" "}
          for account and booking data.
        </p>
      </section>
    </article>
  );
}
