"use client";

import type { BookingOwnerResponse } from "@entities/booking";
import { getBookingStatusPresentation } from "@entities/booking";
import { PermissionGate } from "@entities/user";
import { StudioPermission } from "@shared/lib";
import { Button } from "@shared/ui";

import {
  canCheckIn,
  canMarkNoShow,
  getParticipantDisplayName,
} from "../model/attendance-action";

export interface ParticipantRowProps {
  studioId: number;
  booking: BookingOwnerResponse;
  isPending: boolean;
  isBusy: boolean;
  onCheckIn: (bookingId: number) => void;
  onMarkNoShow: (bookingId: number) => void;
}

export function ParticipantRow({
  studioId,
  booking,
  isPending,
  isBusy,
  onCheckIn,
  onMarkNoShow,
}: ParticipantRowProps) {
  const displayName = getParticipantDisplayName(booking);
  const status = getBookingStatusPresentation(booking);
  const showCheckIn = canCheckIn(booking);
  const showNoShow = canMarkNoShow(booking);
  const contact = [booking.guest_email, booking.guest_phone]
    .filter((value): value is string => Boolean(value?.trim()))
    .join(" · ");

  return (
    <li
      className="rounded-xl border border-neutral-200 bg-white p-4"
      data-testid={`participant-row-${booking.id}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 space-y-1">
          <p className="font-display text-base font-semibold text-neutral-900">
            {displayName}
          </p>
          {contact ? (
            <p className="truncate text-sm text-neutral-600">{contact}</p>
          ) : null}
          <p className="text-xs font-medium text-neutral-500">{status.label}</p>
        </div>

        <PermissionGate
          studioId={studioId}
          permission={StudioPermission.CHECK_IN_BOOKING}
        >
          {showCheckIn || showNoShow ? (
            <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
              {showCheckIn ? (
                <Button
                  type="button"
                  className="min-h-11 w-full sm:w-auto"
                  isLoading={isPending}
                  disabled={isBusy && !isPending}
                  onClick={() => onCheckIn(booking.id)}
                  data-testid={`check-in-${booking.id}`}
                >
                  Check in
                </Button>
              ) : null}
              {showNoShow ? (
                <Button
                  type="button"
                  variant="outline"
                  className="min-h-11 w-full sm:w-auto"
                  isLoading={isPending}
                  disabled={isBusy && !isPending}
                  onClick={() => onMarkNoShow(booking.id)}
                  data-testid={`no-show-${booking.id}`}
                >
                  No-show
                </Button>
              ) : null}
            </div>
          ) : null}
        </PermissionGate>
      </div>
    </li>
  );
}
