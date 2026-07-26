"use client";

import Link from "next/link";

import { useStudio } from "@entities/studio";
import { getUserFacingApiMessage } from "@shared/api";
import {
  Button,
  Card,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import { EditStudioForm } from "./edit-studio-form";

export interface EditStudioPanelProps {
  studioId: number;
}

export function EditStudioPanel({ studioId }: EditStudioPanelProps) {
  const {
    data: studio,
    isLoading,
    isError,
    error,
    refetch,
  } = useStudio(studioId);

  if (isLoading) {
    return <ResourceListSkeleton testId="edit-studio-skeleton" rows={2} />;
  }

  if (isError || !studio) {
    return (
      <ResourceErrorState
        title="Could not load studio"
        message={getUserFacingApiMessage(error)}
        testId="edit-studio-error"
        onRetry={() => {
          void refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6" data-testid="edit-studio-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to Today
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">
          Studio profile
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Slug, timezone, and cancellation policy for {studio.name}.
        </p>
        {studio.slug ? (
          <p className="mt-2 text-sm">
            <Button asChild variant="outline" className="mt-1">
              <Link href={`/s/${studio.slug}`} target="_blank" rel="noreferrer">
                View storefront
              </Link>
            </Button>
          </p>
        ) : null}
      </div>

      <Card className="p-6">
        <EditStudioForm studio={studio} />
      </Card>
    </div>
  );
}
