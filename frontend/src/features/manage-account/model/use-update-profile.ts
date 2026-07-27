"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { CurrentUserUpdate } from "@entities/user";
import { updateCurrentUser } from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

/**
 * PATCH /auth/me and refresh the auth.me cache.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: CurrentUserUpdate) => updateCurrentUser(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.auth.all });
      toast.success("Profile saved");
    },
  });

  return {
    updateProfile: mutation.mutate,
    isSaving: mutation.isPending,
    isSuccess: mutation.isSuccess,
  };
}
