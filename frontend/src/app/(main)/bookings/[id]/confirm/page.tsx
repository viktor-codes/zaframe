"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, Button, Skeleton } from "@/components/ui";
import {
  fetchBooking,
  fetchSlot,
  fetchStudio,
  createCheckoutSession,
  cancelBooking,
  getUserFacingApiMessage,
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
  const queryClient = useQueryClient();
  const id = Number(params.id);

  const [error, setError] = useState<string | null>(null);
  const [showCancelConfirm, setShowCancelConfirm] = useState(false);

  const {
    data: booking,
    isLoading: loadingBooking,
    isError: errorBooking,
  } = useQuery({
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
      setError(getUserFacingApiMessage(err));
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["booking", id] });
      queryClient.invalidateQueries({ queryKey: ["bookings"] });
      setShowCancelConfirm(false);
    },
    onError: (err) => {
      setError(getUserFacingApiMessage(err));
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
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Invalid booking</p>
          <Link
            href="/studios"
            className="mt-2 inline-block text-primary underline"
          >
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (errorBooking) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Booking not found</p>
          <Link
            href="/studios"
            className="mt-2 inline-block text-primary underline"
          >
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (loadingBooking || !booking) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <Skeleton className="mb-6 h-8 w-48" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }

  const isPaid = booking.payment_status === "paid";
  const isCancelled = booking.status === "cancelled";

  if (isCancelled) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <Link
          href="/bookings"
          className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← My bookings
        </Link>
        <div className="rounded-lg border border-neutral-200 bg-neutral-100 p-8 text-center">
          <p className="font-semibold text-neutral-700">Booking cancelled</p>
          <p className="mt-1 text-sm text-neutral-600">
            This booking has been cancelled.
          </p>
          <div className="mt-4 flex justify-center gap-4">
            <Link href="/bookings" className="text-primary underline">
              My bookings
            </Link>
            <Link href="/studios" className="text-primary underline">
              Browse studios
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const isPast = slot ? new Date(slot.start_time) < new Date() : false;
  const canCancel = !isPast && !isCancelled;

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <div className="mb-6 flex items-center gap-4">
        <Link
          href="/bookings"
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← My bookings
        </Link>
      </div>

      <h1 className="text-secondary mb-6 font-display text-2xl font-bold">
        Booking details
      </h1>

      <Card className="mb-6">
        <div className="space-y-4">
          <div>
            <p className="text-sm text-neutral-500">Booking #{booking.id}</p>
            {studio && (
              <p className="text-secondary font-semibold">{studio.name}</p>
            )}
          </div>
          {slot && (
            <>
              <p className="font-medium">{slot.title}</p>
              <p className="text-sm text-neutral-600">
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
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          {error}
        </div>
      )}

      {!isPaid && slot && slot.price_cents > 0 && (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row">
          <Button onClick={handlePay} isLoading={checkoutMutation.isPending}>
            Pay with card (Stripe)
          </Button>
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      )}

      {canCancel && (
        <div className="mb-6">
          {showCancelConfirm ? (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <p className="mb-2 font-medium text-red-800">
                Cancel this booking? This cannot be undone.
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={() => cancelMutation.mutate(id)}
                  isLoading={cancelMutation.isPending}
                  className="border-0 bg-red-600 text-white hover:bg-red-700"
                >
                  Confirm cancel
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setShowCancelConfirm(false)}
                  disabled={cancelMutation.isPending}
                >
                  Keep booking
                </Button>
              </div>
            </div>
          ) : (
            <Button
              variant="ghost"
              onClick={() => setShowCancelConfirm(true)}
              className="text-red-600 hover:bg-red-50 hover:text-red-700"
            >
              Cancel booking
            </Button>
          )}
        </div>
      )}

      {isPaid && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-green-800">
          <p className="font-semibold">Paid</p>
          <p className="mt-1 text-sm">Your booking is confirmed and paid.</p>
        </div>
      )}

      {slot && slot.price_cents === 0 && !isPaid && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-green-800">
          <p className="font-semibold">Free session</p>
          <p className="mt-1 text-sm">
            No payment required. Your booking is confirmed.
          </p>
        </div>
      )}
    </div>
  );
}
