"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { PaymentSuccessPanel } from "@features/book-occurrence";
import { Skeleton } from "@shared/ui";

function SuccessContent() {
  const searchParams = useSearchParams();
  const bookingIdParam = searchParams.get("booking");

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <PaymentSuccessPanel bookingIdParam={bookingIdParam} />
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
