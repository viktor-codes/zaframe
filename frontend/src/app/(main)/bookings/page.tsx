"use client";

import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { RequireAuth } from "@/components/RequireAuth";
import { Card, Button, Skeleton } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { fetchBookings, fetchSlot, fetchStudio } from "@/lib/api";
import type { BookingResponse } from "@/types/booking";

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

function getStatusBadge(status: string, paymentStatus: string | null) {
  if (status === "cancelled") {
    return (
      <span className="rounded-full bg-neutral-200 px-2 py-0.5 text-xs font-medium text-neutral-700">
        Cancelled
      </span>
    );
  }
  if (paymentStatus === "paid") {
    return (
      <span className="rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800">
        Paid
      </span>
    );
  }
  return (
    <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-800">
      Pending
    </span>
  );
}

function BookingsList() {
  const { user } = useAuth();

  const { data: byUser } = useQuery({
    queryKey: ["bookings", "user", user?.id],
    queryFn: () =>
      fetchBookings({ user_id: user!.id, limit: 50 }),
    enabled: !!user?.id,
  });

  const { data: byEmail } = useQuery({
    queryKey: ["bookings", "guest", user?.email],
    queryFn: () =>
      fetchBookings({ guest_email: user!.email, limit: 50 }),
    enabled: !!user?.email,
  });

  const bookings = useMemo(() => {
    const map = new Map<number, BookingResponse>();
    for (const b of byUser ?? []) map.set(b.id, b);
    for (const b of byEmail ?? []) map.set(b.id, b);
    return Array.from(map.values()).sort(
      (a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [byUser, byEmail]);

  const isLoading = (byUser === undefined && !!user?.id) || (byEmail === undefined && !!user?.email);

  if (isLoading) {
    return <BookingsSkeleton />;
  }

  if (bookings.length === 0) {
    return (
      <div className="rounded-lg bg-neutral-100 border border-neutral-200 p-12 text-center text-neutral-600">
        <p className="font-medium">No bookings yet</p>
        <p className="text-sm mt-1">Book a studio session to see your reservations here.</p>
        <Button asChild className="mt-4">
          <Link href="/studios">Browse studios</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {bookings.map((booking) => (
        <BookingCard key={booking.id} booking={booking} />
      ))}
    </div>
  );
}

function BookingCard({ booking }: { booking: BookingResponse }) {
  const { data: slot } = useQuery({
    queryKey: ["slot", booking.slot_id],
    queryFn: () => fetchSlot(booking.slot_id),
  });

  const { data: studio } = useQuery({
    queryKey: ["studio", slot?.studio_id],
    queryFn: () => fetchStudio(slot!.studio_id),
    enabled: !!slot?.studio_id,
  });

  const isPast = slot ? new Date(slot.start_time) < new Date() : false;
  const isCancelled = booking.status === "cancelled";

  return (
    <Link href={`/bookings/${booking.id}/confirm`}>
      <Card variant="interactive">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-semibold text-secondary">
                {studio?.name ?? "—"}
              </span>
              {getStatusBadge(booking.status, booking.payment_status)}
            </div>
            <p className="text-neutral-600 text-sm">
              {slot?.title ?? "Slot"} · {slot ? formatDateTime(slot.start_time) : "—"}
            </p>
            {slot && (
              <p className="font-medium text-primary mt-1">
                {formatPrice(slot.price_cents)}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2">
            {!isCancelled && !isPast && (
              <span className="text-sm text-primary font-medium">
                View details →
              </span>
            )}
          </div>
        </div>
      </Card>
    </Link>
  );
}

function BookingsSkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <Card key={i}>
          <div className="flex justify-between items-start">
            <div className="space-y-2">
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-20" />
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}

export default function BookingsPage() {
  return (
    <RequireAuth>
      <div className="max-w-4xl mx-auto px-6 py-12">
        <h1 className="font-display font-bold text-3xl text-secondary mb-2">
          My bookings
        </h1>
        <p className="text-neutral-600 mb-8">
          View and manage your studio reservations.
        </p>
        <BookingsList />
      </div>
    </RequireAuth>
  );
}
