"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { OrderPaymentSuccessPanel } from "@features/book-course";
import { PaymentSuccessPanel } from "@features/book-occurrence";
import { Skeleton } from "@shared/ui";

function SuccessContent() {
  const searchParams = useSearchParams();
  const orderIdParam = searchParams.get("order");
  const bookingIdParam = searchParams.get("booking");

  // WHY: course checkout redirects with ?order=; drop-in uses ?booking=.
  if (orderIdParam != null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <OrderPaymentSuccessPanel orderIdParam={orderIdParam} />
      </div>
    );
  }

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
