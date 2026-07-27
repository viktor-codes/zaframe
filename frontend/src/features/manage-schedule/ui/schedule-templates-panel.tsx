"use client";

import { useState } from "react";
import Link from "next/link";

import { getUserFacingApiMessage } from "@shared/api";
import { Card, ResourceErrorState, ResourceListSkeleton } from "@shared/ui";

import { suggestGenerateFromTemplates } from "../model/schedule-form-values";
import { useScheduleTemplatesPanel } from "../model/use-schedule-templates-panel";
import { GenerateOccurrencesForm } from "./generate-occurrences-form";
import { TemplateEditWarning } from "./template-edit-warning";
import { TemplatesSection } from "./templates-section";

export interface ScheduleTemplatesPanelProps {
  studioId: number;
  serviceId: number;
}

export function ScheduleTemplatesPanel({
  studioId,
  serviceId,
}: ScheduleTemplatesPanelProps) {
  const [isCreating, setIsCreating] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const panel = useScheduleTemplatesPanel(studioId, serviceId);

  if (panel.isLoading) {
    return (
      <ResourceListSkeleton testId="schedule-templates-skeleton" rows={3} />
    );
  }

  if (panel.isServiceError || !panel.service) {
    return (
      <ResourceErrorState
        title="Could not load service"
        message={getUserFacingApiMessage(panel.serviceError)}
        testId="schedule-service-error"
        onRetry={() => {
          void panel.refetchService();
        }}
      />
    );
  }

  if (panel.isWrongStudio) {
    return (
      <ResourceErrorState
        title="Service not in this studio"
        message="This service belongs to a different studio."
        testId="schedule-wrong-studio"
        onRetry={() => {
          void panel.refetchService();
        }}
      />
    );
  }

  if (panel.isTemplatesError) {
    return (
      <ResourceErrorState
        title="Could not load schedule templates"
        message={getUserFacingApiMessage(panel.templatesError)}
        testId="schedule-templates-error"
        onRetry={() => {
          void panel.refetchTemplates();
        }}
      />
    );
  }

  const { service, templates } = panel;
  const generateKey =
    templates
      .map((t) => `${t.id}:${t.day_of_week}:${t.start_time}`)
      .join("|") || "empty";

  return (
    <div className="space-y-8" data-testid="schedule-templates-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}/services/${serviceId}`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to service
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">
          Schedule templates
        </h1>
        <p className="mt-1 text-sm text-neutral-600">
          Recurring rules for <strong>{service.name}</strong>. Generate sessions
          when you are ready — then edit them in the calendar.
        </p>
      </div>

      <TemplateEditWarning />

      <TemplatesSection
        studioId={studioId}
        serviceId={serviceId}
        templates={templates}
        isCreating={isCreating}
        editingId={editingId}
        onStartCreate={() => {
          setEditingId(null);
          setIsCreating(true);
        }}
        onCancelCreate={() => setIsCreating(false)}
        onEdit={(templateId) => {
          setIsCreating(false);
          setEditingId(templateId);
        }}
        onCancelEdit={() => setEditingId(null)}
      />

      <section aria-labelledby="generate-heading">
        <Card className="space-y-4 p-6">
          <div>
            <h2
              id="generate-heading"
              className="text-lg font-semibold text-neutral-900"
            >
              Generate sessions
            </h2>
            <p className="mt-1 text-sm text-neutral-600">
              Creates concrete calendar slots. Overlapping periods are rejected
              by the API — clear or adjust the calendar first if needed.
            </p>
          </div>
          <GenerateOccurrencesForm
            key={generateKey}
            studioId={studioId}
            serviceId={serviceId}
            initialValues={suggestGenerateFromTemplates(templates)}
          />
        </Card>
      </section>
    </div>
  );
}
