"use client";

import { Suspense } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { GuestBookingConfirmPanel } from "@features/book-occurrence";
import { CancelBookingControls } from "@features/cancel-booking";
import { Skeleton } from "@shared/ui";

function ConfirmContent() {
  const params = useParams();
  const searchParams = useSearchParams();

  return (
    <GuestBookingConfirmPanel
      routeId={params.id}
      accessTokenFromQuery={searchParams.get("access_token")}
      renderCancel={({
        bookingId,
        booking,
        occurrence,
        studio,
        accessToken,
        now,
      }) => (
        <CancelBookingControls
          bookingId={bookingId}
          booking={booking}
          occurrence={occurrence}
          studio={studio}
          accessToken={accessToken}
          now={now}
        />
      )}
    />
  );
}

export default function BookingConfirmPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-6 py-12">
          <Skeleton className="mb-6 h-8 w-48" />
          <Skeleton className="h-32 w-full" />
        </div>
      }
    >
      <ConfirmContent />
    </Suspense>
  );
}
