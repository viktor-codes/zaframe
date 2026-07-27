"use client";

import {
  formatScheduleTemplateSummary,
  type ScheduleTemplateResponse,
} from "@entities/schedule-template";
import { Button } from "@shared/ui";

export interface TemplateListProps {
  templates: readonly ScheduleTemplateResponse[];
  editingId: number | null;
  isDeleting: boolean;
  onEdit: (templateId: number) => void;
  onDelete: (templateId: number) => void;
}

export function TemplateList({
  templates,
  editingId,
  isDeleting,
  onEdit,
  onDelete,
}: TemplateListProps) {
  return (
    <ul className="grid gap-3" data-testid="template-list">
      {templates.map((template) => (
        <li
          key={template.id}
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-white px-4 py-3"
          data-testid={`template-row-${template.id}`}
        >
          <div>
            <p className="text-sm font-semibold text-neutral-900">
              {formatScheduleTemplateSummary(template)}
            </p>
            <p className="mt-0.5 text-xs text-neutral-500">
              From {template.valid_from}
              {template.valid_to
                ? ` · to ${template.valid_to}`
                : " · open-ended"}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={editingId === template.id}
              onClick={() => onEdit(template.id)}
            >
              Edit
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              isLoading={isDeleting}
              disabled={isDeleting}
              onClick={() => {
                if (
                  window.confirm(
                    "Delete this template? Existing calendar sessions stay as they are.",
                  )
                ) {
                  onDelete(template.id);
                }
              }}
            >
              Delete
            </Button>
          </div>
        </li>
      ))}
    </ul>
  );
}
