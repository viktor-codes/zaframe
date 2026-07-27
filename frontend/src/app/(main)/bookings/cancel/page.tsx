import Link from "next/link";

import { parsePositiveIdString } from "@shared/lib/parse-positive-id";
import { Button } from "@shared/ui/button";
import { Card } from "@shared/ui/card";

interface BookingCancelPageProps {
  searchParams: Promise<{ booking?: string; order?: string }>;
}

export default async function BookingCancelPage({
  searchParams,
}: BookingCancelPageProps) {
  const sp = await searchParams;
  // WHY: never interpolate raw query into href — reject floats / junk.
  const bookingId = parsePositiveIdString(sp.booking ?? null);
  const orderId = parsePositiveIdString(sp.order ?? null);

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Card className="py-12 text-center" data-testid="payment-cancelled">
        <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
          Payment cancelled
        </h1>
        <p className="mb-8 text-neutral-600">
          {orderId != null
            ? "Your payment was cancelled. Your course order is still pending. You can complete the payment later or browse other studios."
            : "Your payment was cancelled. Your booking is still pending. You can complete the payment later or browse other studios."}
        </p>
        <div className="flex flex-col justify-center gap-4 sm:flex-row">
          {orderId != null ? (
            <Button asChild>
              <Link href="/account/orders">View my orders</Link>
            </Button>
          ) : null}
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
