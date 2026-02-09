"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Card, Button } from "@/components/ui";

export default function BookingSuccessPage() {
  const searchParams = useSearchParams();
  const bookingId = searchParams.get("booking");

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <Card className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 text-green-600 mb-6">
          <svg
            className="w-8 h-8"
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
        <h1 className="font-display font-bold text-2xl text-secondary mb-2">
          Payment successful
        </h1>
        <p className="text-neutral-600 mb-8">
          Your booking has been confirmed and paid. We&apos;ll send a confirmation
          to your email.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
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
