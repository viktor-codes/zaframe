"use client";

import Link from "next/link";

import {
  getStudioDisplayName,
  type StudioOnboardingStep,
  type StudioWithRoleResponse,
} from "@entities/studio";
import { getUserFacingApiMessage } from "@shared/api";
import { Button, Card } from "@shared/ui";

import { useMyStudiosDashboard } from "../model/use-my-studios-dashboard";
import {
  MyStudiosEmptyState,
  MyStudiosErrorState,
  MyStudiosSkeleton,
} from "./my-studios-states";

export function MyStudiosPanel() {
  const { rows, spotlight, isLoading, isError, error, refetch } =
    useMyStudiosDashboard();

  if (isLoading) {
    return <MyStudiosSkeleton />;
  }

  if (isError) {
    return (
      <MyStudiosErrorState
        message={getUserFacingApiMessage(error)}
        onRetry={refetch}
      />
    );
  }

  if (rows.length === 0) {
    return <MyStudiosEmptyState />;
  }

  return (
    <div className="space-y-6" data-testid="my-studios-panel">
      {spotlight ? (
        <OnboardingCallout studio={spotlight.studio} step={spotlight.step} />
      ) : null}

      <div className="flex items-center justify-between gap-4">
        <h2 className="text-secondary text-lg font-semibold">My studios</h2>
        <Button asChild>
          <Link href="/dashboard/studios/new">Add studio</Link>
        </Button>
      </div>

      <div className="grid gap-4">
        {rows.map(({ studio, step }) => (
          <StudioMembershipCard key={studio.id} studio={studio} step={step} />
        ))}
      </div>
    </div>
  );
}

function OnboardingCallout({
  studio,
  step,
}: {
  studio: StudioWithRoleResponse;
  step: StudioOnboardingStep;
}) {
  return (
    <section
      className="rounded-2xl border border-teal-200 bg-teal-50/80 px-5 py-4"
      data-testid="studio-onboarding-callout"
      data-step={step.id}
    >
      <p className="text-xs font-semibold tracking-wide text-teal-800 uppercase">
        Next step · {getStudioDisplayName(studio)}
      </p>
      <h2 className="mt-1 font-display text-xl font-bold text-neutral-900">
        {step.title}
      </h2>
      <p className="mt-1 text-sm text-neutral-700">{step.description}</p>
      <Button asChild className="mt-4">
        <Link href={step.href}>{step.ctaLabel}</Link>
      </Button>
    </section>
  );
}

function StudioMembershipCard({
  studio,
  step,
}: {
  studio: StudioWithRoleResponse;
  step: StudioOnboardingStep | null;
}) {
  return (
    <Link href={`/dashboard/studios/${studio.id}`}>
      <Card variant="interactive" data-testid="studio-membership-card">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="text-secondary font-semibold">
              {getStudioDisplayName(studio)}
            </h3>
            {studio.description ? (
              <p className="mt-1 line-clamp-2 text-sm text-neutral-600">
                {studio.description}
              </p>
            ) : null}
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-neutral-500">
              <span className="rounded-md border border-neutral-200 bg-neutral-50 px-2 py-0.5 capitalize">
                {studio.role}
              </span>
              {studio.is_active ? (
                <span className="text-green-600">Active</span>
              ) : (
                <span>Inactive</span>
              )}
              {step && step.id !== "ready" ? (
                <span className="text-teal-800">{step.title}</span>
              ) : null}
            </div>
          </div>
          <span className="shrink-0 text-sm font-medium text-primary">
            Manage →
          </span>
        </div>
      </Card>
    </Link>
  );
}
