"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { StudioMemberCreate, StudioMemberUpdate } from "@entities/studio";
import { invalidateStudioMembers } from "@entities/studio";
import {
  addStudioMember,
  removeStudioMember,
  updateStudioMember,
} from "@shared/api";
import { toast } from "@shared/ui";

export function useMemberMutations(studioId: number) {
  const queryClient = useQueryClient();

  const invalidate = () => {
    invalidateStudioMembers(queryClient, studioId);
  };

  const add = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: StudioMemberCreate) => addStudioMember(studioId, data),
    onSuccess: () => {
      invalidate();
      toast.success("Team member added");
    },
  });

  const update = useMutation({
    meta: { toastOnError: true },
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: number;
      data: StudioMemberUpdate;
    }) => updateStudioMember(studioId, memberId, data),
    onSuccess: () => {
      invalidate();
      toast.success("Role updated");
    },
  });

  const remove = useMutation({
    meta: { toastOnError: true },
    mutationFn: (memberId: number) => removeStudioMember(studioId, memberId),
    onSuccess: () => {
      invalidate();
      toast.success("Team member removed");
    },
  });

  return {
    addMember: add.mutate,
    isAdding: add.isPending,
    updateMemberRole: update.mutate,
    isUpdating: update.isPending,
    removeMember: remove.mutate,
    isRemoving: remove.isPending,
    pendingMemberId:
      update.isPending && update.variables
        ? update.variables.memberId
        : remove.isPending && remove.variables != null
          ? remove.variables
          : null,
  };
}
