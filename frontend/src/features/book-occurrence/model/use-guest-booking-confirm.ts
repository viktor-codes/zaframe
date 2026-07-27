"use client";

import { useEffect, useState } from "react";
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
  readGuestAccessTokenFromLocation,
  syncGuestAccessTokenFromLocation,
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
  /** Guest resource token when present; null for session-authenticated customers. */
  accessToken: string | null;
  error: string | null;
  clearError: () => void;
  isPaying: boolean;
  pay: () => void;
}

function peekUrlAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return readGuestAccessTokenFromLocation(
    window.location.href,
    window.location.hash,
  );
}

/**
 * Load guest/self booking for `/bookings/{id}/confirm` using sessionStorage
 * and optional deep link (`#access_token=` preferred; `?access_token=` legacy).
 */
export function useGuestBookingConfirm(
  routeId: unknown,
): UseGuestBookingConfirmResult {
  const bookingId = parseBookingRouteId(routeId);
  const actions = useGuestBookingActions(bookingId);
  const [urlTokenPeek, setUrlTokenPeek] = useState<string | null>(null);

  useEffect(() => {
    if (bookingId == null) return;
    const synced = syncGuestAccessTokenFromLocation(
      bookingId,
      persistGuestBookingAccessToken,
    );
    setUrlTokenPeek(synced ?? peekUrlAccessToken());
  }, [bookingId]);

  const guestSnapshot =
    bookingId != null ? getGuestBookingSnapshot(bookingId) : null;
  // WHY: first paint may run before the effect persists the deep-link token.
  const accessToken =
    (bookingId != null ? getGuestBookingAccessToken(bookingId) : null) ??
    urlTokenPeek ??
    peekUrlAccessToken();
  const isGuestSession = accessToken != null;

  const {
    data: booking,
    isLoading: loadingBooking,
    isError: errorBooking,
  } = useQuery({
    queryKey: queryKeys.booking.detail(bookingId ?? 0),
    queryFn: ({ signal }) => {
      syncGuestAccessTokenFromLocation(
        bookingId!,
        persistGuestBookingAccessToken,
      );
      const token =
        getGuestBookingAccessToken(bookingId!) ?? peekUrlAccessToken();
      return fetchBooking(bookingId!, { accessToken: token, signal });
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
    queryFn: ({ signal }) =>
      fetchOccurrence(resolvedBooking!.occurrence_id, { signal }),
    enabled: !!resolvedBooking?.occurrence_id,
  });

  const { data: studio } = useQuery({
    queryKey: queryKeys.studio.detail(occurrence?.studio_id),
    queryFn: ({ signal }) => fetchStudio(occurrence!.studio_id, { signal }),
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
    accessToken: isMissingId ? null : accessToken,
    error: isMissingId ? null : actions.error,
    clearError: actions.clearError,
    isPaying: !isMissingId && actions.isPaying,
    pay: actions.pay,
  };
}
