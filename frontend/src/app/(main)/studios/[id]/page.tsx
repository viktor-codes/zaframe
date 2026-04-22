"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Card, Button, Skeleton, Input } from "@/components/ui";
import { fetchStudio, fetchStudioSlots, getUserFacingApiMessage } from "@/lib/api";

function toISOStartOfDay(d: Date): string {
  const c = new Date(d);
  c.setHours(0, 0, 0, 0);
  return c.toISOString();
}

function toISOEndOfDay(d: Date): string {
  const c = new Date(d);
  c.setHours(23, 59, 59, 999);
  return c.toISOString();
}

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(cents / 100);
}

function formatDateTime(iso: string): { date: string; time: string } {
  const d = new Date(iso);
  return {
    date: d.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric",
    }),
    time: d.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
    }),
  };
}

export default function StudioDetailPage() {
  const params = useParams();
  const id = Number(params.id);

  const today = useMemo(() => {
    const t = new Date();
    return t.toISOString().slice(0, 10);
  }, []);

  const [dateFilter, setDateFilter] = useState<string>(today);

  const dateRange = useMemo(() => {
    if (!dateFilter) return undefined;
    const d = new Date(dateFilter);
    if (Number.isNaN(d.getTime())) return undefined;
    return {
      start_from: toISOStartOfDay(d),
      start_to: toISOEndOfDay(d),
    };
  }, [dateFilter]);

  const {
    data: studio,
    isLoading: loadingStudio,
    isError: errorStudio,
    error: studioError,
  } = useQuery({
    queryKey: ["studio", id],
    queryFn: () => fetchStudio(id),
    enabled: !Number.isNaN(id),
  });

  const {
    data: slots,
    isLoading: loadingSlots,
    isError: errorSlots,
  } = useQuery({
    queryKey: [
      "studio",
      id,
      "slots",
      dateRange?.start_from,
      dateRange?.start_to,
    ],
    queryFn: () =>
      fetchStudioSlots(id, {
        is_active: true,
        ...(dateRange ?? {}),
      }),
    enabled: !Number.isNaN(id) && !!studio,
  });

  if (Number.isNaN(id)) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Invalid studio ID</p>
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

  if (errorStudio) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          <p className="font-semibold">Failed to load studio</p>
          <p className="mt-1 text-sm">
            {getUserFacingApiMessage(studioError)}
          </p>
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

  if (loadingStudio || !studio) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-12">
        <StudioDetailSkeleton />
      </div>
    );
  }

  const now = new Date();
  const upcomingSlots =
    slots?.filter((s) => new Date(s.start_time) >= now) ?? [];

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <Link
        href="/studios"
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        ← Back to studios
      </Link>

      <div className="mb-10">
        <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
          {studio.name}
        </h1>
        {studio.description && (
          <p className="mb-4 text-neutral-600">{studio.description}</p>
        )}
        <div className="flex flex-wrap gap-4 text-sm text-neutral-600">
          {studio.address && <span title="Address">{studio.address}</span>}
          {studio.phone && (
            <a href={`tel:${studio.phone}`} className="hover:text-primary">
              {studio.phone}
            </a>
          )}
          {studio.email && (
            <a href={`mailto:${studio.email}`} className="hover:text-primary">
              {studio.email}
            </a>
          )}
        </div>
      </div>

      <section>
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-secondary font-display text-xl font-semibold">
            Available slots
          </h2>
          <label className="flex items-center gap-2 text-sm text-neutral-600">
            <span>Date:</span>
            <Input
              type="date"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              min={today}
              className="w-auto max-w-[180px]"
            />
          </label>
        </div>

        {errorSlots ? (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-amber-800">
            <p className="text-sm">Could not load schedule. Try again later.</p>
          </div>
        ) : loadingSlots ? (
          <SlotsSkeleton />
        ) : upcomingSlots.length === 0 ? (
          <div className="rounded-lg border border-neutral-200 bg-neutral-100 p-8 text-center text-neutral-600">
            <p className="font-medium">No available slots</p>
            <p className="mt-1 text-sm">
              There are no upcoming sessions. Check back later.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {upcomingSlots.map((slot) => {
              const { date, time } = formatDateTime(slot.start_time);
              const endTime = new Date(slot.end_time).toLocaleTimeString(
                "en-US",
                { hour: "2-digit", minute: "2-digit" },
              );
              return (
                <Card key={slot.id} variant="interactive">
                  <div className="space-y-2">
                    <h3 className="text-secondary font-semibold">
                      {slot.title}
                    </h3>
                    {slot.description && (
                      <p className="line-clamp-2 text-sm text-neutral-600">
                        {slot.description}
                      </p>
                    )}
                    <p className="text-sm text-neutral-500">
                      {date} · {time} – {endTime}
                    </p>
                    <p className="font-semibold text-primary">
                      {formatPrice(slot.price_cents)}
                    </p>
                    <Button asChild className="mt-2 px-4 py-2 text-sm">
                      <Link href={`/studios/${id}/book?slot=${slot.id}`}>
                        Book this slot
                      </Link>
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function StudioDetailSkeleton() {
  return (
    <div className="space-y-8">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-4 w-full max-w-2xl" />
      <Skeleton className="h-4 w-full max-w-xl" />
      <div className="pt-4">
        <Skeleton className="mb-4 h-6 w-40" />
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <div className="space-y-2">
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-4 w-1/4" />
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

function SlotsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <Card key={i}>
          <div className="space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-1/2" />
            <Skeleton className="h-4 w-1/4" />
          </div>
        </Card>
      ))}
    </div>
  );
}
