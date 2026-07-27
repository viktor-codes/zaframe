"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { checkInBooking, markBookingNoShow } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

/**
 * Check-in / no-show mutations; invalidate occurrence + studio lists on success.
 */
export function useAttendanceMutations(studioId: number, occurrenceId: number) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    void queryClient.invalidateQueries({
      queryKey: queryKeys.occurrence.bookings(occurrenceId),
    });
    void queryClient.invalidateQueries({
      queryKey: queryKeys.occurrence.detail(occurrenceId),
    });
    void queryClient.invalidateQueries({
      queryKey: queryKeys.studio.occurrencesRoot(studioId),
    });
  };

  const checkInMutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (bookingId: number) => checkInBooking(bookingId),
    onSuccess: () => {
      invalidate();
      toast.success("Checked in");
    },
  });

  const noShowMutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (bookingId: number) => markBookingNoShow(bookingId),
    onSuccess: () => {
      invalidate();
      toast.success("Marked as no-show");
    },
  });

  return {
    checkIn: checkInMutation.mutate,
    markNoShow: noShowMutation.mutate,
    pendingBookingId: checkInMutation.isPending
      ? checkInMutation.variables
      : noShowMutation.isPending
        ? noShowMutation.variables
        : null,
    isBusy: checkInMutation.isPending || noShowMutation.isPending,
  };
}
