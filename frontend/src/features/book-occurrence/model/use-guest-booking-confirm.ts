"use client";

import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  fetchBooking,
  fetchOccurrence,
  fetchStudio,
} from "@shared/api";
import {
  getGuestBookingAccessToken,
  getGuestBookingSnapshot,
  persistGuestBookingAccessToken,
  queryKeys,
  updateGuestBookingSnapshot,
  type GuestBookingSnapshot,
} from "@shared/lib";
import type { BookingDetailResponse } from "@entities/booking";

import {
  parseBookingRouteId,
  syncGuestAccessTokenFromQuery,
} from "./sync-guest-access-token";
import { useGuestBookingActions } from "./use-guest-booking-actions";

export type ResolvedGuestBooking =
  | BookingDetailResponse
  | GuestBookingSnapshot;

export interface UseGuestBookingConfirmResult {
  bookingId: number | null;
  booking: ResolvedGuestBooking | null;
  occurrence: Awaited<ReturnType<typeof fetchOccurrence>> | undefined;
  studio: Awaited<ReturnType<typeof fetchStudio>> | undefined;
  isLoading: boolean;
  isNotFound: boolean;
  isGuestSession: boolean;
  error: string | null;
  clearError: () => void;
  isPaying: boolean;
  isCancelling: boolean;
  pay: () => void;
  cancel: () => void;
}

/**
 * Load guest/self booking for `/bookings/{id}/confirm` using session token
 * and optional `?access_token=` deep link.
 */
export function useGuestBookingConfirm(
  routeId: unknown,
  accessTokenFromQuery: string | null,
): UseGuestBookingConfirmResult {
  const bookingId = parseBookingRouteId(routeId);
  const actions = useGuestBookingActions(bookingId);

  useEffect(() => {
    if (bookingId == null) return;
    syncGuestAccessTokenFromQuery(
      bookingId,
      accessTokenFromQuery,
      persistGuestBookingAccessToken,
    );
  }, [bookingId, accessTokenFromQuery]);

  const guestSnapshot =
    bookingId != null ? getGuestBookingSnapshot(bookingId) : null;
  // WHY: first paint may run before the effect persists `?access_token=` — prefer query.
  const accessToken =
    (bookingId != null ? getGuestBookingAccessToken(bookingId) : null) ??
    accessTokenFromQuery;
  const isGuestSession = accessToken != null;

  const {
    data: booking,
    isLoading: loadingBooking,
    isError: errorBooking,
  } = useQuery({
    queryKey: queryKeys.booking.detail(bookingId ?? 0),
    queryFn: () => {
      const token =
        getGuestBookingAccessToken(bookingId!) ?? accessTokenFromQuery;
      if (accessTokenFromQuery) {
        persistGuestBookingAccessToken(bookingId!, accessTokenFromQuery);
      }
      return fetchBooking(bookingId!, { accessToken: token });
    },
    enabled: bookingId != null,
    retry: false,
  });

  useEffect(() => {
    if (bookingId == null || !booking) return;
    updateGuestBookingSnapshot(bookingId, {
      occurrence_id: booking.occurrence_id,
      guest_name: booking.guest_name ?? null,
      guest_email: booking.guest_email ?? null,
      status: booking.status,
      payment_status: booking.payment_status ?? null,
      reserved_until: booking.reserved_until ?? null,
    });
  }, [booking, bookingId]);

  // WHY: snapshot is optimistic paint only while loading — never mask a failed GET.
  const resolvedBooking: ResolvedGuestBooking | null =
    booking ?? (loadingBooking ? guestSnapshot : null);

  const { data: occurrence } = useQuery({
    queryKey: queryKeys.occurrence.detail(resolvedBooking?.occurrence_id),
    queryFn: () => fetchOccurrence(resolvedBooking!.occurrence_id),
    enabled: !!resolvedBooking?.occurrence_id,
  });

  const { data: studio } = useQuery({
    queryKey: queryKeys.studio.detail(occurrence?.studio_id),
    queryFn: () => fetchStudio(occurrence!.studio_id),
    enabled: !!occurrence?.studio_id,
  });

  const isMissingId = bookingId == null;

  return {
    bookingId,
    booking: isMissingId ? null : resolvedBooking,
    occurrence: isMissingId ? undefined : occurrence,
    studio: isMissingId ? undefined : studio,
    isLoading:
      !isMissingId && loadingBooking && !booking && !guestSnapshot,
    isNotFound: isMissingId || Boolean(errorBooking && !booking),
    isGuestSession: !isMissingId && isGuestSession,
    error: isMissingId ? null : actions.error,
    clearError: actions.clearError,
    isPaying: !isMissingId && actions.isPaying,
    isCancelling: !isMissingId && actions.isCancelling,
    pay: actions.pay,
    cancel: actions.cancel,
  };
}
