"use client";

import { useState } from "react";

import type {
  ScheduleTemplateCreate,
  ScheduleTemplateResponse,
  ScheduleTemplateUpdate,
} from "@entities/schedule-template";
import { Button } from "@shared/ui";

import {
  parseCreateTemplate,
  parseUpdateTemplate,
} from "../model/schedule-form-schema";
import {
  emptyTemplateForm,
  templateToFormValues,
  type TemplateFormValues,
} from "../model/schedule-form-values";
import { TemplateEditWarning } from "./template-edit-warning";
import { TemplateFormFields } from "./template-form-fields";

type TemplateFormProps = {
  isSaving: boolean;
  onCancel: () => void;
} & (
  | {
      mode: "create";
      template?: undefined;
      onSubmit: (data: ScheduleTemplateCreate) => void;
    }
  | {
      mode: "edit";
      template: ScheduleTemplateResponse;
      onSubmit: (data: ScheduleTemplateUpdate) => void;
    }
);

export type { TemplateFormProps };

export function TemplateForm(props: TemplateFormProps) {
  const { mode, isSaving, onCancel, onSubmit } = props;
  const template = mode === "edit" ? props.template : undefined;

  const [values, setValues] = useState<TemplateFormValues>(() =>
    mode === "edit" && template
      ? templateToFormValues(template)
      : emptyTemplateForm(),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof TemplateFormValues, string>>
  >({});

  return (
    <form
      className="space-y-4 rounded-xl border border-neutral-200 bg-white p-4"
      data-testid={
        mode === "edit" ? "edit-template-form" : "create-template-form"
      }
      onSubmit={(event) => {
        event.preventDefault();
        if (mode === "edit") {
          const parsed = parseUpdateTemplate(values);
          setErrors(parsed.errors);
          if (!parsed.data) return;
          onSubmit(parsed.data);
          return;
        }
        const parsed = parseCreateTemplate(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        onSubmit(parsed.data);
      }}
    >
      {mode === "edit" ? <TemplateEditWarning template={template} /> : null}

      <TemplateFormFields
        values={values}
        errors={errors}
        onChange={(key, value) =>
          setValues((prev) => ({ ...prev, [key]: value }))
        }
        idPrefix={mode === "edit" ? "edit-template" : "create-template"}
      />

      <div className="flex justify-end gap-3">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSaving}
        >
          Cancel
        </Button>
        <Button type="submit" isLoading={isSaving}>
          {mode === "edit" ? "Save template" : "Add template"}
        </Button>
      </div>
    </form>
  );
}
