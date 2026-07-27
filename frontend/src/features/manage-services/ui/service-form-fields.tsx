"use client";

import {
  isServiceCategory,
  SERVICE_CATEGORIES,
  SERVICE_TYPE,
} from "@entities/service";
import { Input, Textarea } from "@shared/ui";

import type { ServiceFormValues } from "../model/service-form-values";

export interface ServiceFormFieldsProps {
  values: ServiceFormValues;
  errors: Partial<Record<keyof ServiceFormValues, string>>;
  onChange: <K extends keyof ServiceFormValues>(
    key: K,
    value: ServiceFormValues[K],
  ) => void;
}

export function ServiceFormFields({
  values,
  errors,
  onChange,
}: ServiceFormFieldsProps) {
  return (
    <div className="space-y-4">
      <Input
        label="Name"
        required
        value={values.name}
        onChange={(event) => onChange("name", event.target.value)}
        error={errors.name}
        maxLength={200}
        placeholder="Morning Flow"
      />

      <Textarea
        label="Description"
        value={values.description}
        onChange={(event) => onChange("description", event.target.value)}
        error={errors.description}
        rows={3}
        placeholder="A calm 60-minute class for all levels."
      />

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label
            htmlFor="service-type"
            className="mb-2 block text-sm font-medium text-neutral-700"
          >
            Type
          </label>
          <select
            id="service-type"
            value={values.type}
            onChange={(event) => onChange("type", event.target.value)}
            className="w-full rounded-lg border-2 border-neutral-200 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          >
            <option value={SERVICE_TYPE.SINGLE}>Single class</option>
            <option value={SERVICE_TYPE.COURSE}>Course</option>
          </select>
        </div>

        <div>
          <label
            htmlFor="service-category"
            className="mb-2 block text-sm font-medium text-neutral-700"
          >
            Category
          </label>
          <select
            id="service-category"
            value={values.category}
            onChange={(event) => {
              const next = event.target.value;
              if (isServiceCategory(next)) {
                onChange("category", next);
              }
            }}
            className="w-full rounded-lg border-2 border-neutral-200 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          >
            {SERVICE_CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {category.replaceAll("_", " ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Duration (minutes)"
          type="number"
          required
          min={1}
          value={values.duration_minutes}
          onChange={(event) => onChange("duration_minutes", event.target.value)}
          error={errors.duration_minutes}
        />
        <Input
          label="Max capacity"
          type="number"
          required
          min={1}
          value={values.max_capacity}
          onChange={(event) => onChange("max_capacity", event.target.value)}
          error={errors.max_capacity}
        />
      </div>

      <Input
        label="Drop-in price (EUR)"
        required
        inputMode="decimal"
        value={values.price_euros}
        onChange={(event) => onChange("price_euros", event.target.value)}
        error={errors.price_euros}
        placeholder="25.00"
      />

      {values.type === SERVICE_TYPE.COURSE ? (
        <Input
          label="Course price (EUR)"
          required
          inputMode="decimal"
          value={values.price_course_euros}
          onChange={(event) =>
            onChange("price_course_euros", event.target.value)
          }
          error={errors.price_course_euros}
          placeholder="180.00"
        />
      ) : null}
    </div>
  );
}
