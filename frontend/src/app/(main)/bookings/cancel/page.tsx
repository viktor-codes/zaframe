"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, Button } from "@/components/ui";

export default function BookingCancelPage() {
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("booking");

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <Card className="text-center py-12">
        <h1 className="font-display font-bold text-2xl text-secondary mb-2">
          Payment cancelled
        </h1>
        <p className="text-neutral-600 mb-8">
          Your payment was cancelled. Your booking is still pending. You can
          complete the payment later or browse other studios.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          {bookingId && (
            <Button asChild>
              <Link href={`/bookings/${bookingId}/confirm`}>
                Back to booking
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
