"use client";

import { useState } from "react";
import Link from "next/link";

import { DAY_OF_WEEK_OPTIONS } from "@entities/schedule-template";
import { Button, Input } from "@shared/ui";

import { parseGenerateOccurrences } from "../model/schedule-form-schema";
import type { GenerateFormValues } from "../model/schedule-form-values";
import { useGenerateOccurrences } from "../model/use-schedule-mutations";

export interface GenerateOccurrencesFormProps {
  studioId: number;
  serviceId: number;
  initialValues: GenerateFormValues;
}

export function GenerateOccurrencesForm({
  studioId,
  serviceId,
  initialValues,
}: GenerateOccurrencesFormProps) {
  const { generate, isGenerating } = useGenerateOccurrences(
    studioId,
    serviceId,
  );
  const [values, setValues] = useState<GenerateFormValues>(initialValues);
  const [errors, setErrors] = useState<
    Partial<Record<keyof GenerateFormValues, string>>
  >({});

  function toggleDay(day: string) {
    setValues((prev) => {
      const hasDay = prev.days.includes(day);
      return {
        ...prev,
        days: hasDay
          ? prev.days.filter((value) => value !== day)
          : [...prev.days, day].sort((a, b) => Number(a) - Number(b)),
      };
    });
  }

  return (
    <form
      className="space-y-4"
      data-testid="generate-occurrences-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseGenerateOccurrences(values, serviceId);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        generate(parsed.data);
      }}
    >
      <div>
        <p className="mb-2 text-sm font-medium text-neutral-700">Days</p>
        <div className="flex flex-wrap gap-2">
          {DAY_OF_WEEK_OPTIONS.map((option) => {
            const key = String(option.value);
            const isSelected = values.days.includes(key);
            return (
              <button
                key={option.value}
                type="button"
                onClick={() => toggleDay(key)}
                className={`rounded-lg border-2 px-3 py-1.5 text-sm font-medium ${
                  isSelected
                    ? "border-teal-500 bg-teal-50 text-teal-900"
                    : "border-neutral-200 bg-white text-neutral-700 hover:border-neutral-300"
                }`}
                aria-pressed={isSelected}
                data-testid={`generate-day-${option.value}`}
              >
                {option.shortLabel}
              </button>
            );
          })}
        </div>
        {errors.days ? (
          <p className="mt-1 text-sm text-red-600">{errors.days}</p>
        ) : null}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Input
          label="Start time"
          type="time"
          required
          value={values.start_time}
          onChange={(event) =>
            setValues((prev) => ({ ...prev, start_time: event.target.value }))
          }
          error={errors.start_time}
          data-testid="generate-start-time"
        />
        <Input
          label="Weeks to generate"
          type="number"
          min={1}
          max={52}
          required
          value={values.weeks_count}
          onChange={(event) =>
            setValues((prev) => ({
              ...prev,
              weeks_count: event.target.value,
            }))
          }
          error={errors.weeks_count}
          data-testid="generate-weeks-count"
        />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link
          href={`/dashboard/studios/${studioId}/calendar`}
          className="text-sm font-medium text-primary hover:text-primary-dark"
        >
          Open calendar →
        </Link>
        <Button type="submit" isLoading={isGenerating}>
          Generate sessions
        </Button>
      </div>
    </form>
  );
}
