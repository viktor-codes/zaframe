"use client";

import { Suspense, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Card, Button, Input, Skeleton } from "@shared/ui";
import { createBooking, fetchStudio, fetchStudioOccurrences } from "@shared/api";
import {
  OccurrenceStatus,
  queryKeys,
  storeGuestBookingAccess,
} from "@shared/lib";

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

function BookPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const studioId = Number(params.id);
  const occurrenceIdParam = searchParams.get("occurrence");
  const occurrenceId = occurrenceIdParam ? Number(occurrenceIdParam) : null;

  const [form, setForm] = useState({
    guest_name: "",
    guest_email: "",
    guest_phone: "",
  });

  const occurrenceFilters = useMemo(
    () => ({ status: OccurrenceStatus.SCHEDULED }),
    [],
  );

  const { data: studio } = useQuery({
    queryKey: queryKeys.studio.detail(studioId),
    queryFn: () => fetchStudio(studioId),
    enabled: !!studioId && !Number.isNaN(studioId),
  });

  const { data: occurrences } = useQuery({
    queryKey: queryKeys.studio.occurrences(studioId, occurrenceFilters),
    queryFn: () => fetchStudioOccurrences(studioId, occurrenceFilters),
    enabled: !!studio,
  });

  const occurrence = occurrences?.find((o) => o.id === occurrenceId);

  const createMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: (booking) => {
      storeGuestBookingAccess(booking.id, booking.access_token, {
        id: booking.id,
        occurrence_id: booking.occurrence_id,
        guest_name: booking.guest_name ?? null,
        guest_email: booking.guest_email ?? null,
        status: booking.status,
        payment_status: booking.payment_status ?? null,
        reserved_until: booking.reserved_until ?? null,
      });
      window.location.href = `/bookings/${booking.id}/confirm`;
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!occurrenceId || !occurrence) return;
    createMutation.mutate({
      occurrence_id: occurrenceId,
      guest_name: form.guest_name.trim(),
      guest_email: form.guest_email.trim(),
      guest_phone: form.guest_phone.trim() || undefined,
      booking_type: "single",
      service_id: occurrence.service_id,
    });
  };

  if (Number.isNaN(studioId) || !studioId) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Invalid studio</p>
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

  if (!occurrenceId) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-800">
          <p className="font-semibold">Select a session</p>
          <p className="mt-1 text-sm">
            Choose a time from the studio page to book.
          </p>
          <Link
            href={`/studios/${studioId}`}
            className="mt-2 inline-block text-primary underline"
          >
            View studio schedule
          </Link>
        </div>
      </div>
    );
  }

  if (!studio || !occurrence) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 w-48 rounded bg-neutral-200" />
          <div className="h-32 rounded bg-neutral-200" />
        </div>
      </div>
    );
  }

  const now = new Date();
  if (new Date(occurrence.start_time) < now) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-6 text-amber-800">
          <p className="font-semibold">Session has passed</p>
          <p className="mt-1 text-sm">
            This session is no longer available. Please choose another.
          </p>
          <Link
            href={`/studios/${studioId}`}
            className="mt-2 inline-block text-primary underline"
          >
            View studio schedule
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <Link
        href={`/studios/${studioId}`}
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        ← Back to {studio.name}
      </Link>

      <h1 className="text-secondary mb-6 font-display text-2xl font-bold">
        Book a session
      </h1>

      <div className="grid gap-8 lg:grid-cols-2">
        <Card>
          <h2 className="text-secondary mb-2 font-semibold">Booking details</h2>
          <p className="mb-1 text-sm text-neutral-600">{studio.name}</p>
          <p className="text-secondary font-medium">{occurrence.title}</p>
          <p className="mt-1 text-sm text-neutral-500">
            {formatDateTime(occurrence.start_time)}
          </p>
          <p className="mt-2 font-semibold text-primary">
            {formatPrice(occurrence.price_cents)}
          </p>
        </Card>

        <Card>
          <h2 className="text-secondary mb-4 font-semibold">
            Your information
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Name"
              type="text"
              required
              placeholder="Your name"
              value={form.guest_name}
              onChange={(e) =>
                setForm((f) => ({ ...f, guest_name: e.target.value }))
              }
              autoComplete="name"
            />
            <Input
              label="Email"
              type="email"
              required
              placeholder="your@email.com"
              value={form.guest_email}
              onChange={(e) =>
                setForm((f) => ({ ...f, guest_email: e.target.value }))
              }
              autoComplete="email"
              data-testid="guest-email-input"
            />
            <Input
              label="Phone (optional)"
              type="tel"
              placeholder="+1 234 567 8900"
              value={form.guest_phone}
              onChange={(e) =>
                setForm((f) => ({ ...f, guest_phone: e.target.value }))
              }
              autoComplete="tel"
            />
            <Button
              type="submit"
              isLoading={createMutation.isPending}
              fullWidth
              className="mt-4"
              data-testid="submit-booking-button"
            >
              Confirm booking
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}

export default function BookPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-2xl px-6 py-12">
          <Skeleton className="h-64 w-full" />
        </div>
      }
    >
      <BookPageContent />
    </Suspense>
  );
}
