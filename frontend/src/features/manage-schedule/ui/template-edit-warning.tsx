import {
  DEFAULT_TEMPLATE_EDIT_WARNING,
  getScheduleTemplateEditWarning,
  type ScheduleTemplateResponse,
} from "@entities/schedule-template";

export interface TemplateEditWarningProps {
  template?: Pick<ScheduleTemplateResponse, "edit_behavior"> | null;
}

export function TemplateEditWarning({ template }: TemplateEditWarningProps) {
  const message = template
    ? getScheduleTemplateEditWarning(template)
    : DEFAULT_TEMPLATE_EDIT_WARNING;

  return (
    <p
      className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900"
      data-testid="template-edit-warning"
      role="status"
    >
      {message}
    </p>
  );
}
