"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { parsePositiveIdString } from "@shared/lib";
import { Card, Button, Skeleton } from "@shared/ui";

function CancelContent() {
  const searchParams = useSearchParams();
  // WHY: never interpolate raw query into href — reject floats / junk.
  const bookingId = parsePositiveIdString(searchParams.get("booking"));

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Card className="py-12 text-center">
        <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
          Payment cancelled
        </h1>
        <p className="mb-8 text-neutral-600">
          Your payment was cancelled. Your booking is still pending. You can
          complete the payment later or browse other studios.
        </p>
        <div className="flex flex-col justify-center gap-4 sm:flex-row">
          {bookingId != null ? (
            <Button asChild>
              <Link href={`/bookings/${bookingId}/confirm`}>
                Back to booking
              </Link>
            </Button>
          ) : null}
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default function BookingCancelPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-6 py-12">
          <Skeleton className="h-48 w-full" />
        </div>
      }
    >
      <CancelContent />
    </Suspense>
  );
}
