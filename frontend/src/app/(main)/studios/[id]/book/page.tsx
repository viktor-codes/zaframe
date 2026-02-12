"use client";

import { Suspense, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Card, Button, Input, Skeleton } from "@/components/ui";
import {
  fetchStudio,
  fetchStudioSlots,
  createBooking,
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

function BookPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const studioId = Number(params.id);
  const slotIdParam = searchParams.get("slot");
  const slotId = slotIdParam ? Number(slotIdParam) : null;

  const [form, setForm] = useState({
    guest_name: "",
    guest_email: "",
    guest_phone: "",
  });

  const { data: studio } = useQuery({
    queryKey: ["studio", studioId],
    queryFn: () => fetchStudio(studioId),
    enabled: !!studioId && !Number.isNaN(studioId),
  });

  const { data: slots } = useQuery({
    queryKey: ["studio", studioId, "slots"],
    queryFn: () => fetchStudioSlots(studioId, { is_active: true }),
    enabled: !!studio,
  });

  const slot = slots?.find((s) => s.id === slotId);

  const createMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: (booking) => {
      window.location.href = `/bookings/${booking.id}/confirm`;
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!slotId || !slot) return;
    createMutation.mutate({
      slot_id: slotId,
      guest_name: form.guest_name.trim(),
      guest_email: form.guest_email.trim(),
      guest_phone: form.guest_phone.trim() || undefined,
    });
  };

  if (Number.isNaN(studioId) || !studioId) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-red-50 border border-red-200 p-6 text-red-800">
          <p className="font-semibold">Invalid studio</p>
          <Link href="/studios" className="text-primary underline mt-2 inline-block">
            Back to studios
          </Link>
        </div>
      </div>
    );
  }

  if (!slotId) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-6 text-amber-800">
          <p className="font-semibold">Select a slot</p>
          <p className="text-sm mt-1">
            Choose a time slot from the studio page to book.
          </p>
          <Link
            href={`/studios/${studioId}`}
            className="text-primary underline mt-2 inline-block"
          >
            View studio schedule
          </Link>
        </div>
      </div>
    );
  }

  if (!studio || !slot) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-neutral-200 rounded w-48" />
          <div className="h-32 bg-neutral-200 rounded" />
        </div>
      </div>
    );
  }

  const now = new Date();
  if (new Date(slot.start_time) < now) {
    return (
      <div className="max-w-2xl mx-auto px-6 py-12">
        <div className="rounded-lg bg-amber-50 border border-amber-200 p-6 text-amber-800">
          <p className="font-semibold">Slot has passed</p>
          <p className="text-sm mt-1">
            This slot is no longer available. Please choose another.
          </p>
          <Link
            href={`/studios/${studioId}`}
            className="text-primary underline mt-2 inline-block"
          >
            View studio schedule
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-6 py-12">
      <Link
        href={`/studios/${studioId}`}
        className="text-primary hover:text-primary-dark text-sm font-medium mb-6 inline-block"
      >
        ← Back to {studio.name}
      </Link>

      <h1 className="font-display font-bold text-2xl text-secondary mb-6">
        Book a session
      </h1>

      <div className="grid gap-8 lg:grid-cols-2">
        <Card>
          <h2 className="font-semibold text-secondary mb-2">Booking details</h2>
          <p className="text-neutral-600 text-sm mb-1">{studio.name}</p>
          <p className="font-medium text-secondary">{slot.title}</p>
          <p className="text-neutral-500 text-sm mt-1">
            {formatDateTime(slot.start_time)}
          </p>
          <p className="font-semibold text-primary mt-2">
            {formatPrice(slot.price_cents)}
          </p>
        </Card>

        <Card>
          <h2 className="font-semibold text-secondary mb-4">
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
    <Suspense fallback={<div className="max-w-2xl mx-auto px-6 py-12"><Skeleton className="h-64 w-full" /></div>}>
      <BookPageContent />
    </Suspense>
  );
}
