"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { cancelBooking } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

export interface UseCancelBookingOptions {
  /** Guest JWT for confirm-page cancel without session auth. */
  accessToken?: string | null;
  onSuccess?: () => void;
}

/**
 * Cancels a booking and refreshes account / detail caches.
 * Errors are toasted by the app MutationCache — do not double-toast here.
 */
export function useCancelBooking(options: UseCancelBookingOptions = {}) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (bookingId: number) =>
      cancelBooking(bookingId, {
        accessToken: options.accessToken,
      }),
    onSuccess: (_data, bookingId) => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.booking.detail(bookingId),
      });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.bookings.all,
      });
      toast.success("Booking cancelled");
      options.onSuccess?.();
    },
  });

  return {
    cancelBooking: (bookingId: number) => mutation.mutate(bookingId),
    isCancelling: mutation.isPending,
  };
}
