"use client";

import type { ScheduleTemplateResponse } from "@entities/schedule-template";
import { Button, ResourceEmptyState } from "@shared/ui";

import { useScheduleTemplateMutations } from "../model/use-schedule-mutations";
import { TemplateForm } from "./template-form";
import { TemplateList } from "./template-list";

export interface TemplatesSectionProps {
  studioId: number;
  serviceId: number;
  templates: readonly ScheduleTemplateResponse[];
  isCreating: boolean;
  editingId: number | null;
  onStartCreate: () => void;
  onCancelCreate: () => void;
  onEdit: (templateId: number) => void;
  onCancelEdit: () => void;
}

export function TemplatesSection({
  studioId,
  serviceId,
  templates,
  isCreating,
  editingId,
  onStartCreate,
  onCancelCreate,
  onEdit,
  onCancelEdit,
}: TemplatesSectionProps) {
  const {
    createTemplate,
    updateTemplate,
    deleteTemplate,
    isSaving,
    isDeleting,
  } = useScheduleTemplateMutations(studioId, serviceId);

  const editingTemplate =
    editingId == null
      ? undefined
      : templates.find((template) => template.id === editingId);

  return (
    <section className="space-y-4" aria-labelledby="templates-heading">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2
          id="templates-heading"
          className="text-lg font-semibold text-neutral-900"
        >
          Templates
        </h2>
        {!isCreating && editingId == null ? (
          <Button type="button" onClick={onStartCreate}>
            Add template
          </Button>
        ) : null}
      </div>

      {templates.length === 0 && !isCreating ? (
        <ResourceEmptyState
          title="No templates yet"
          description="Add a weekly rule (day + time), then generate sessions for the weeks ahead. Use Add template above to start."
          testId="templates-empty"
        />
      ) : (
        <TemplateList
          templates={templates}
          editingId={editingId}
          isDeleting={isDeleting}
          onEdit={onEdit}
          onDelete={(templateId) => {
            deleteTemplate(templateId, {
              onSuccess: () => {
                if (editingId === templateId) onCancelEdit();
              },
            });
          }}
        />
      )}

      {isCreating ? (
        <TemplateForm
          mode="create"
          isSaving={isSaving}
          onCancel={onCancelCreate}
          onSubmit={(data) => {
            createTemplate(data, { onSuccess: onCancelCreate });
          }}
        />
      ) : null}

      {editingTemplate ? (
        <TemplateForm
          key={editingTemplate.id}
          mode="edit"
          template={editingTemplate}
          isSaving={isSaving}
          onCancel={onCancelEdit}
          onSubmit={(data) => {
            updateTemplate(
              { templateId: editingTemplate.id, data },
              { onSuccess: onCancelEdit },
            );
          }}
        />
      ) : null}
    </section>
  );
}
