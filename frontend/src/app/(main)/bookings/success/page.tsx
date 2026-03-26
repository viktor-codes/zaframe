"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, Button, Skeleton } from "@/components/ui";

function SuccessContent() {
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("booking");

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Card className="py-12 text-center">
        <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600">
          <svg
            className="h-8 w-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
          Payment successful
        </h1>
        <p className="mb-8 text-neutral-600">
          Your booking has been confirmed and paid. We&apos;ll send a
          confirmation to your email.
        </p>
        <div className="flex flex-col justify-center gap-4 sm:flex-row">
          {bookingId && (
            <Button asChild>
              <Link href={`/bookings/${bookingId}/confirm`}>
                View booking details
              </Link>
            </Button>
          )}
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function BookingSuccessPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-6 py-12">
          <Skeleton className="h-48 w-full" />
        </div>
      }
    >
      <SuccessContent />
    </Suspense>
  );
}
