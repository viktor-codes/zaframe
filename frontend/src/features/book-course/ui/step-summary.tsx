"use client";

import Link from "next/link";
import type {
  ServiceAvailabilityResponse,
  ServiceAvailabilityScheduleItem,
} from "@entities/service";
import { formatMoneyFromCents } from "@shared/lib";
import { Button } from "@shared/ui";

import type { GuestDetails } from "../model/guest-details-schema";
import { CourseAvailabilityBanner } from "./course-availability-banner";
import { CourseSchedulePreview } from "./course-schedule-preview";

export interface StepSummaryProps {
  studioName: string;
  serviceName: string;
  sessionCount: number;
  priceCents: number;
  guest: GuestDetails;
  availability: ServiceAvailabilityResponse | null;
  schedule: ServiceAvailabilityScheduleItem[];
  error: string | null;
  isHardBlocked?: boolean;
  heldOrderId?: number | null;
  isPaying: boolean;
  canProceed: boolean;
  studioSlug: string;
  onBack: () => void;
  onPay: () => void;
}

export function StepSummary({
  studioName,
  serviceName,
  sessionCount,
  priceCents,
  guest,
  availability,
  schedule,
  error,
  isHardBlocked = false,
  heldOrderId = null,
  isPaying,
  canProceed,
  studioSlug,
  onBack,
  onPay,
}: StepSummaryProps) {
  const isFree = priceCents === 0;
  const payDisabled = isHardBlocked || !canProceed;

  return (
    <div className="space-y-6" data-testid="book-course-step-summary">
      {availability ? (
        <CourseAvailabilityBanner availability={availability} />
      ) : null}

      <div className="rounded-2xl border border-neutral-200 bg-white p-5">
        <h3 className="font-display text-lg font-semibold text-neutral-900">
          Course summary
        </h3>
        <dl className="mt-4 space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Studio</dt>
            <dd className="text-right font-medium text-neutral-900">
              {studioName}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Course</dt>
            <dd className="text-right font-medium text-neutral-900">
              {serviceName}
            </dd>
          </div>
          <div className="flex justify-between gap-4">
            <dt className="text-neutral-500">Sessions</dt>
            <dd className="text-right font-medium text-neutral-900">
              {sessionCount === 1 ? "1 session" : `${sessionCount} sessions`}
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
              {isFree ? "Free" : formatMoneyFromCents(priceCents)}
            </dd>
          </div>
        </dl>
      </div>

      <div>
        <h4 className="mb-2 text-xs font-semibold tracking-wide text-neutral-500 uppercase">
          Included dates
        </h4>
        <CourseSchedulePreview schedule={schedule} />
      </div>

      {error ? (
        <div
          className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          data-testid={
            isHardBlocked
              ? "book-course-hard-block-error"
              : "book-course-checkout-error"
          }
        >
          <p>{error}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {isHardBlocked ? (
              <Button type="button" variant="outline" asChild>
                <Link
                  href={`/s/${encodeURIComponent(studioSlug)}`}
                  data-testid="book-course-back-to-studio"
                >
                  Back to studio
                </Link>
              </Button>
            ) : null}
            {heldOrderId != null ? (
              <Button type="button" variant="outline" asChild>
                <Link
                  href="/account/orders"
                  data-testid="book-course-open-orders"
                >
                  View my orders
                </Link>
              </Button>
            ) : null}
          </div>
        </div>
      ) : null}

      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-between">
        <Button
          type="button"
          variant="ghost"
          onClick={onBack}
          disabled={isPaying || heldOrderId != null}
        >
          Back
        </Button>
        <Button
          type="button"
          isLoading={isPaying}
          onClick={onPay}
          disabled={payDisabled}
          data-testid="submit-course-booking-button"
        >
          {isFree
            ? "Confirm free course"
            : heldOrderId != null
              ? "Retry payment"
              : "Pay with Stripe"}
        </Button>
      </div>
    </div>
  );
}
