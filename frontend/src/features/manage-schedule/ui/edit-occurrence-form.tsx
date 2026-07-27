"use client";

import { useState } from "react";

import type { OccurrenceResponse } from "@entities/occurrence";
import { Button, Input } from "@shared/ui";

import { toDatetimeLocalValue } from "../model/datetime-local";
import {
  parseOccurrenceEdit,
  type OccurrenceEditFormValues,
} from "../model/occurrence-edit-schema";
import { useUpdateCalendarOccurrence } from "../model/use-calendar-mutations";

export interface EditOccurrenceFormProps {
  studioId: number;
  occurrence: OccurrenceResponse;
  onCancel: () => void;
  onSaved: () => void;
}

export function EditOccurrenceForm({
  studioId,
  occurrence,
  onCancel,
  onSaved,
}: EditOccurrenceFormProps) {
  const { updateOccurrence, isSaving } = useUpdateCalendarOccurrence(studioId);
  const [values, setValues] = useState<OccurrenceEditFormValues>({
    title: occurrence.title,
    start_time: toDatetimeLocalValue(occurrence.start_time),
    end_time: toDatetimeLocalValue(occurrence.end_time),
    max_capacity: String(occurrence.max_capacity),
  });
  const [errors, setErrors] = useState<
    Partial<Record<keyof OccurrenceEditFormValues, string>>
  >({});

  return (
    <form
      className="mt-3 space-y-3 border-t border-neutral-200 pt-3"
      data-testid="edit-occurrence-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseOccurrenceEdit(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        updateOccurrence(
          { occurrenceId: occurrence.id, data: parsed.data },
          { onSuccess: onSaved },
        );
      }}
    >
      <Input
        label="Title"
        required
        value={values.title}
        onChange={(event) =>
          setValues((prev) => ({ ...prev, title: event.target.value }))
        }
        error={errors.title}
      />
      <div className="grid gap-3 sm:grid-cols-2">
        <Input
          label="Start"
          type="datetime-local"
          required
          value={values.start_time}
          onChange={(event) =>
            setValues((prev) => ({ ...prev, start_time: event.target.value }))
          }
          error={errors.start_time}
        />
        <Input
          label="End"
          type="datetime-local"
          required
          value={values.end_time}
          onChange={(event) =>
            setValues((prev) => ({ ...prev, end_time: event.target.value }))
          }
          error={errors.end_time}
        />
      </div>
      <Input
        label="Max capacity"
        type="number"
        min={1}
        required
        value={values.max_capacity}
        onChange={(event) =>
          setValues((prev) => ({
            ...prev,
            max_capacity: event.target.value,
          }))
        }
        error={errors.max_capacity}
      />
      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isSaving}
        >
          Close
        </Button>
        <Button type="submit" isLoading={isSaving}>
          Save session
        </Button>
      </div>
    </form>
  );
}
