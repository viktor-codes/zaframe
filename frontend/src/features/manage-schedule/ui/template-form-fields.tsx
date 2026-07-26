"use client";

import { DAY_OF_WEEK_OPTIONS } from "@entities/schedule-template";
import { Input } from "@shared/ui";

import type { TemplateFormValues } from "../model/schedule-form-values";

export interface TemplateFormFieldsProps {
  values: TemplateFormValues;
  errors: Partial<Record<keyof TemplateFormValues, string>>;
  onChange: <K extends keyof TemplateFormValues>(
    key: K,
    value: TemplateFormValues[K],
  ) => void;
  idPrefix?: string;
}

export function TemplateFormFields({
  values,
  errors,
  onChange,
  idPrefix = "template",
}: TemplateFormFieldsProps) {
  return (
    <div className="space-y-4">
      <div>
        <label
          htmlFor={`${idPrefix}-day`}
          className="mb-2 block text-sm font-medium text-neutral-700"
        >
          Day of week
        </label>
        <select
          id={`${idPrefix}-day`}
          value={values.day_of_week}
          onChange={(event) => onChange("day_of_week", event.target.value)}
          className="w-full rounded-lg border-2 border-neutral-200 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          data-testid={`${idPrefix}-day`}
        >
          {DAY_OF_WEEK_OPTIONS.map((option) => (
            <option key={option.value} value={String(option.value)}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.day_of_week ? (
          <p className="mt-1 text-sm text-red-600">{errors.day_of_week}</p>
        ) : null}
      </div>

      <Input
        label="Start time"
        type="time"
        required
        value={values.start_time}
        onChange={(event) => onChange("start_time", event.target.value)}
        error={errors.start_time}
        data-testid={`${idPrefix}-start-time`}
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Valid from"
          type="date"
          required
          value={values.valid_from}
          onChange={(event) => onChange("valid_from", event.target.value)}
          error={errors.valid_from}
          data-testid={`${idPrefix}-valid-from`}
        />
        <Input
          label="Valid to (optional)"
          type="date"
          value={values.valid_to}
          onChange={(event) => onChange("valid_to", event.target.value)}
          error={errors.valid_to}
          data-testid={`${idPrefix}-valid-to`}
        />
      </div>
    </div>
  );
}
