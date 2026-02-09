"use client";

import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, Button, Skeleton } from "@/components/ui";
import {
  fetchBooking,
  fetchSlot,
  fetchStudio,
  createCheckoutSession,
} from "@/lib/api";

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function BookingConfirmPage() {
  const params = useParams();
  const id = Number(params.id);

  const [error, setError] = useState<string | null>(null);

  const { data: booking, isLoading: loadingBooking, isError: errorBooking } = useQuery({
    queryKey: ["booking", id],
    queryFn: () => fetchBooking(id),
  });

  const { data: slot } = useQuery({
    queryKey: ["slot", booking?.slot_id],
    queryFn: () => fetchSlot(booking!.slot_id),
    enabled: !!booking?.slot_id,
  });

  const { data: studio } = useQuery({
    queryKey: ["studio", slot?.studio_id],
    queryFn: () => fetchStudio(slot!.studio_id),
    enabled: !!slot?.studio_id,
  });

  const checkoutMutation = useMutation({
    mutationFn: createCheckoutSession,
    onSuccess: (data) => {
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    },
    onError: (err) => {
      setError(err instanceof Error ? err.message : "Payment failed");
    },
  });

  const handlePay = () => {
    if (!booking?.id) return;
    setError(null);
    const base = typeof window !== "undefined" ? window.location.origin : "";
    checkoutMutation.mutate({
      booking_id: booking.id,
      success_url: `${base}/bookings/success?booking=${booking.id}`,
      cancel_url: `${base}/bookings/cancel?booking=${booking.id}`,
    });
  };

  if (Number.isNaN(id)) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
          <p className="font-semibold">Invalid booking</p>
          <Link href="/studios" className="text-primary underline mt-2 inline-block">
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (errorBooking) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
          <p className="font-semibold">Booking not found</p>
          <Link href="/studios" className="text-primary underline mt-2 inline-block">
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (loadingBooking || !booking) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const isPaid = booking.payment_status === "paid";
  const isCancelled = booking.status === "cancelled";

  if (isCancelled) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-neutral-100 border border-neutral-200 p-8 text-center">
          <p className="font-semibold text-neutral-700">Booking cancelled</p>
          <p className="text-sm text-neutral-600 mt-1">
            This booking has been cancelled.
          </p>
          <Link href="/studios" className="text-primary underline mt-4 inline-block">
            Browse studios
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <h1 className="font-display font-bold text-2xl text-secondary mb-6">
        Booking confirmed
      </h1>

      <Card className="mb-6">
        <div className="space-y-4">
          <div>
            <p className="text-sm text-neutral-500">Booking #{booking.id}</p>
            {studio && (
              <p className="font-semibold text-secondary">{studio.name}</p>
            )}
          </div>
          {slot && (
            <>
              <p className="font-medium">{slot.title}</p>
              <p className="text-neutral-600 text-sm">
                {formatDateTime(slot.start_time)}
              </p>
              <p className="font-semibold text-primary">
                {formatPrice(slot.price_cents)}
              </p>
            </>
          )}
          {booking.guest_name && (
            <p className="text-sm text-neutral-600">
              Guest: {booking.guest_name}
              {booking.guest_email && ` (${booking.guest_email})`}
            </p>
          )}
        </div>
      </Card>

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-red-800 mb-6">
          {error}
        </div>
      )}

      {!isPaid && slot && slot.price_cents > 0 && (
        <div className="flex flex-col sm:flex-row gap-4">
          <Button
            onClick={handlePay}
            isLoading={checkoutMutation.isPending}
          >
            Pay with card (Stripe)
          </Button>
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      )}

      {isPaid && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-green-800">
          <p className="font-semibold">Paid</p>
          <p className="text-sm mt-1">Your booking is confirmed and paid.</p>
        </div>
      )}

      {slot && slot.price_cents === 0 && !isPaid && (
        <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-green-800">
          <p className="font-semibold">Free session</p>
          <p className="text-sm mt-1">No payment required. Your booking is confirmed.</p>
        </div>
      )}
    </div>
  );
}
