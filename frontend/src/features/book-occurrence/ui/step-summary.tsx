"use client";

import type { OccurrenceResponse } from "@entities/occurrence";
import { Button } from "@shared/ui";

import type { GuestDetails } from "../model/guest-details-schema";

export interface StepSummaryProps {
  studioName: string;
  serviceName: string;
  occurrence: OccurrenceResponse;
  guest: GuestDetails;
  error: string | null;
  isPaying: boolean;
  onBack: () => void;
  onPay: () => void;
}

function formatPrice(cents: number): string {
  return new Intl.NumberFormat("en-EU", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(cents / 100);
}

function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    weekday: "short",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function StepSummary({
  studioName,
  serviceName,
  occurrence,
  guest,
  error,
  isPaying,
  onBack,
  onPay,
}: StepSummaryProps) {
  return (
    <div className="space-y-6" data-testid="book-step-summary">
      <div className="rounded-2xl border border-neutral-200 bg-white p-5">
        <h3 className="font-display text-lg font-semibold text-neutral-900">
          Booking summary
        </h3>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Studio</dt>
            <dd className="text-right font-medium text-neutral-900">
              {studioName}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Class</dt>
            <dd className="text-right font-medium text-neutral-900">
              {serviceName}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Session</dt>
            <dd className="text-right font-medium text-neutral-900">
              {occurrence.title}
              <br />
              <span className="font-normal text-neutral-600">
                {formatDateTime(occurrence.start_time)}
              </span>
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Guest</dt>
            <dd className="text-right font-medium text-neutral-900">
              {guest.guest_name}
              <br />
              <span className="font-normal text-neutral-600">
                {guest.guest_email}
              </span>
            </dd>
          </div>
          <div className="flex justify-between gap-4 border-t border-neutral-100 pt-3">
            <dt className="font-semibold text-neutral-700">Total</dt>
            <dd className="font-mono text-lg font-bold text-teal-600">
              {formatPrice(occurrence.price_cents)}
            </dd>
          </div>
        </dl>
      </div>

      {error ? (
        <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {error}
        </div>
      ) : null}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
        <Button type="button" variant="ghost" onClick={onBack} disabled={isPaying}>
          Back
        </Button>
        <Button
          type="button"
          isLoading={isPaying}
          onClick={onPay}
          data-testid="submit-booking-button"
        >
          Pay with Stripe
        </Button>
      </div>
    </div>
  );
}
