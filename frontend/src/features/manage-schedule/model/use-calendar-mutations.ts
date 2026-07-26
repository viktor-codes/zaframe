"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { OccurrenceUpdate } from "@entities/occurrence";
import { updateOccurrence } from "@shared/api";
import { toast } from "@shared/ui";

function invalidateStudioOccurrences(
  queryClient: ReturnType<typeof useQueryClient>,
  studioId: number,
) {
  void queryClient.invalidateQueries({
    queryKey: ["studio", studioId, "occurrences"],
  });
}

export function useUpdateCalendarOccurrence(studioId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: ({
      occurrenceId,
      data,
    }: {
      occurrenceId: number;
      data: OccurrenceUpdate;
    }) => updateOccurrence(occurrenceId, data),
    onSuccess: () => {
      invalidateStudioOccurrences(queryClient, studioId);
      toast.success("Session updated");
    },
  });

  return {
    updateOccurrence: mutation.mutate,
    isSaving: mutation.isPending,
  };
}

export function useCancelCalendarOccurrence(studioId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: ({
      occurrenceId,
      data,
    }: {
      occurrenceId: number;
      data: OccurrenceUpdate;
    }) => updateOccurrence(occurrenceId, data),
    onSuccess: () => {
      invalidateStudioOccurrences(queryClient, studioId);
      toast.success("Session cancelled");
    },
  });

  return {
    cancelOccurrence: mutation.mutate,
    isCancelling: mutation.isPending,
  };
}
