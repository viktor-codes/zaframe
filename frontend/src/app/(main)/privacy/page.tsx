import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy | ZeeFrame",
  description: "How ZeeFrame handles account, booking, and payment data.",
};

export default function PrivacyPage() {
  return (
    <article
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="privacy-page"
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
        Privacy notice
      </h1>
      <p className="mb-6 text-sm text-neutral-600">
        Short notice for closed beta. Last updated 27 Jul 2026.
      </p>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">What we collect</h2>
        <p>
          Account details you provide (email, name, optional phone, marketing
          preference), booking and course order records, and payment ledger
          metadata needed to run checkout with Stripe.
        </p>
      </section>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">
          Why we process it
        </h2>
        <p>
          To sign you in (email OTP), reserve seats, confirm paid bookings,
          email transactional updates, and operate studio dashboards you use.
        </p>
      </section>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">Processors</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>
            <strong>Stripe</strong> — payment checkout and Connect payouts.
          </li>
          <li>
            <strong>Resend</strong> — transactional email (OTP and notices).
          </li>
        </ul>
      </section>

      <section className="mb-8 space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">Your choices</h2>
        <p>
          In Account → Profile you can update marketing consent, download a copy
          of your data, or delete your account. Deletion soft-closes your login;
          studios retain booking/payment history for their records.
        </p>
        <p>
          Cookie details:{" "}
          <Link href="/cookies" className="text-primary underline">
            Cookies notice
          </Link>
          .
        </p>
      </section>

      <section className="space-y-3 text-sm text-neutral-700">
        <h2 className="text-base font-semibold text-zinc-900">Contact</h2>
        <p>
          For a data subject request outside the in-app export, email the address
          used on your account or contact the studio that holds your booking.
        </p>
      </section>
    </article>
  );
}
