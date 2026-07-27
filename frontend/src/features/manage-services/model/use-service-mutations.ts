"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import type { ServiceCreate, ServiceUpdate } from "@entities/service";
import { invalidateStudioServices } from "@entities/studio";
import {
  createService,
  deactivateService,
  updateService,
} from "@shared/api";
import { queryKeys, ServiceVisibility } from "@shared/lib";
import { toast } from "@shared/ui";

function invalidateServiceCaches(
  queryClient: ReturnType<typeof useQueryClient>,
  studioId: number,
  serviceId?: number,
) {
  invalidateStudioServices(queryClient, studioId);
  void queryClient.invalidateQueries({ queryKey: queryKeys.studios.my });
  if (serviceId != null) {
    void queryClient.invalidateQueries({
      queryKey: queryKeys.service.detail(serviceId),
    });
  }
}

export function useCreateService(studioId: number) {
  const queryClient = useQueryClient();
  const router = useRouter();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: ServiceCreate) => createService(data),
    onSuccess: (service) => {
      invalidateServiceCaches(queryClient, studioId, service.id);
      toast.success("Service created as draft");
      router.push(
        `/dashboard/studios/${studioId}/services/${service.id}`,
      );
    },
  });

  return {
    createService: mutation.mutate,
    isSaving: mutation.isPending,
  };
}

export function useUpdateService(studioId: number, serviceId: number) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    meta: { toastOnError: true },
    mutationFn: (data: ServiceUpdate) => updateService(serviceId, data),
    onSuccess: () => {
      invalidateServiceCaches(queryClient, studioId, serviceId);
      toast.success("Service saved");
    },
  });

  return {
    updateService: mutation.mutate,
    isSaving: mutation.isPending,
  };
}

export function useServiceVisibilityActions(
  studioId: number,
  serviceId: number,
) {
  const queryClient = useQueryClient();

  const publish = useMutation({
    meta: { toastOnError: true },
    mutationFn: () =>
      updateService(serviceId, { visibility: ServiceVisibility.PUBLISHED }),
    onSuccess: () => {
      invalidateServiceCaches(queryClient, studioId, serviceId);
      toast.success("Service published");
    },
  });

  const unpublish = useMutation({
    meta: { toastOnError: true },
    mutationFn: () =>
      updateService(serviceId, { visibility: ServiceVisibility.DRAFT }),
    onSuccess: () => {
      invalidateServiceCaches(queryClient, studioId, serviceId);
      toast.success("Service moved back to draft");
    },
  });

  const archive = useMutation({
    meta: { toastOnError: true },
    mutationFn: () => deactivateService(serviceId),
    onSuccess: () => {
      invalidateServiceCaches(queryClient, studioId, serviceId);
      toast.success("Service archived");
    },
  });

  return {
    publish: publish.mutate,
    unpublish: unpublish.mutate,
    archive: archive.mutate,
    isPending:
      publish.isPending || unpublish.isPending || archive.isPending,
  };
}
