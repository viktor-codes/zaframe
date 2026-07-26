"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type {
  ScheduleGenerateRequest,
  ScheduleTemplateCreate,
  ScheduleTemplateUpdate,
} from "@entities/schedule-template";
import {
  createScheduleTemplate,
  deleteScheduleTemplate,
  generateStudioOccurrences,
  updateScheduleTemplate,
} from "@shared/api";
import { queryKeys } from "@shared/lib";
import { toast } from "@shared/ui";

function invalidateScheduleCaches(
  queryClient: ReturnType<typeof useQueryClient>,
  studioId: number,
  serviceId: number,
) {
  void queryClient.invalidateQueries({
    queryKey: queryKeys.service.scheduleTemplates(serviceId),
  });
  void queryClient.invalidateQueries({
    queryKey: ["studio", studioId, "occurrences"],
  });
}

export function useScheduleTemplateMutations(
  studioId: number,
  serviceId: number,
) {
  const queryClient = useQueryClient();

  const create = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: ScheduleTemplateCreate) =>
      createScheduleTemplate(serviceId, data),
    onSuccess: () => {
      invalidateScheduleCaches(queryClient, studioId, serviceId);
      toast.success("Template saved");
    },
  });

  const update = useMutation({
    meta: { toastOnError: true },
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: number;
      data: ScheduleTemplateUpdate;
    }) => updateScheduleTemplate(templateId, data),
    onSuccess: () => {
      invalidateScheduleCaches(queryClient, studioId, serviceId);
      toast.success("Template updated — existing sessions unchanged");
    },
  });

  const remove = useMutation({
    meta: { toastOnError: true },
    mutationFn: (templateId: number) => deleteScheduleTemplate(templateId),
    onSuccess: () => {
      invalidateScheduleCaches(queryClient, studioId, serviceId);
      toast.success("Template deleted");
    },
  });

  return {
    createTemplate: create.mutate,
    updateTemplate: update.mutate,
    deleteTemplate: remove.mutate,
    isSaving: create.isPending || update.isPending,
    isDeleting: remove.isPending,
  };
}

export function useGenerateOccurrences(studioId: number, serviceId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: ScheduleGenerateRequest) =>
      generateStudioOccurrences(studioId, data),
    onSuccess: (occurrences) => {
      invalidateScheduleCaches(queryClient, studioId, serviceId);
      toast.success(
        occurrences.length === 1
          ? "1 session generated"
          : `${occurrences.length} sessions generated`,
      );
    },
  });

  return {
    generate: mutation.mutate,
    isGenerating: mutation.isPending,
  };
}
