"use client";

import { useQuery } from "@tanstack/react-query";

import { fetchMyStudios } from "@shared/api";
import { useAuth } from "@shared/auth";
import { queryKeys } from "@shared/lib";

/**
 * Memberships for the signed-in user (`GET /studios/my`).
 * Powers StudioSwitcher and dashboard studio lists.
 */
export function useMyStudios() {
  const { user, isInitialized } = useAuth();

  return useQuery({
    queryKey: queryKeys.studios.my,
    queryFn: fetchMyStudios,
    enabled: isInitialized && user != null,
  });
}
