"use client";

import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { deleteCurrentUserAccount } from "@shared/api";
import { useAuth } from "@shared/auth";
import { toast } from "@shared/ui";

/**
 * Soft-delete the current account, scrub local session, redirect home.
 */
export function useDeleteAccount() {
  const router = useRouter();
  const { clearSession } = useAuth();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: () => deleteCurrentUserAccount(),
    onSuccess: () => {
      clearSession();
      toast.success("Your account has been deleted");
      router.push("/");
    },
  });

  return {
    deleteAccount: mutation.mutate,
    isDeleting: mutation.isPending,
  };
}
