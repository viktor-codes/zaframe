"use client";

import { Skeleton } from "@shared/ui";

import { getStudioDisplayName } from "../model/studio";
import type { StudioWithRoleResponse } from "../model/types";

export interface StudioSwitcherProps {
  studios: ReadonlyArray<Pick<StudioWithRoleResponse, "id" | "name">>;
  /** Active studio from the URL; `null` on `/dashboard` (list). */
  selectedStudioId: number | null;
  onStudioSelect: (studioId: number) => void;
  isLoading?: boolean;
  className?: string;
}

/**
 * Desktop-first studio picker for the dashboard shell.
 * Presentational — parent supplies memberships and navigation.
 */
export function StudioSwitcher({
  studios,
  selectedStudioId,
  onStudioSelect,
  isLoading = false,
  className = "",
}: StudioSwitcherProps) {
  if (isLoading) {
    return (
      <div
        className={`min-w-40 ${className}`}
        data-testid="studio-switcher-loading"
      >
        <Skeleton className="h-9 w-full" />
      </div>
    );
  }

  if (studios.length === 0) {
    return null;
  }

  if (studios.length === 1) {
    const only = studios[0];
    return (
      <p
        className={`truncate text-sm font-semibold text-neutral-800 ${className}`}
        data-testid="studio-switcher"
        title={getStudioDisplayName(only)}
      >
        {getStudioDisplayName(only)}
      </p>
    );
  }

  const selectValue =
    selectedStudioId != null &&
    studios.some((studio) => studio.id === selectedStudioId)
      ? String(selectedStudioId)
      : "";

  return (
    <div className={`min-w-40 ${className}`} data-testid="studio-switcher">
      <label htmlFor="studio-switcher" className="sr-only">
        Switch studio
      </label>
      <select
        id="studio-switcher"
        value={selectValue}
        onChange={(event) => {
          const nextId = Number(event.target.value);
          if (Number.isFinite(nextId) && nextId > 0) {
            onStudioSelect(nextId);
          }
        }}
        className="w-full rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-800 outline-none focus:border-teal-400 focus:ring-2 focus:ring-teal-100"
      >
        {selectedStudioId == null || selectValue === "" ? (
          <option value="" disabled>
            Select studio
          </option>
        ) : null}
        {studios.map((studio) => (
          <option key={studio.id} value={studio.id}>
            {getStudioDisplayName(studio)}
          </option>
        ))}
      </select>
    </div>
  );
}
