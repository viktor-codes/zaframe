"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import type { StudioCreate } from "@entities/studio";
import { createStudio } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

/**
 * POST /studios then open the profile step (onboarding spine).
 */
export function useCreateStudio() {
  const queryClient = useQueryClient();
  const router = useRouter();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: Omit<StudioCreate, "owner_id">) => createStudio(data),
    onSuccess: (studio) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.studios.all });
      toast.success("Studio created");
      router.push(`/dashboard/studios/${studio.id}/profile`);
    },
  });

  return {
    createStudio: mutation.mutate,
    isSaving: mutation.isPending,
  };
}
