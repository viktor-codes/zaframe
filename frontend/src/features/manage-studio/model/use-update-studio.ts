"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { StudioUpdate } from "@entities/studio";
import { updateStudio } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

/**
 * PATCH /studios/{id} and refresh membership + detail caches.
 */
export function useUpdateStudio(studioId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: StudioUpdate) => updateStudio(studioId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.studios.all });
      void queryClient.invalidateQueries({
        queryKey: queryKeys.studio.detail(studioId),
      });
      toast.success("Studio profile saved");
    },
  });

  return {
    updateStudio: mutation.mutate,
    isSaving: mutation.isPending,
  };
}
