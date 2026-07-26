"use client";

import { useState } from "react";

import type { OccurrenceResponse } from "@entities/occurrence";
import { Button, Textarea } from "@shared/ui";

import {
  parseOccurrenceCancel,
  type OccurrenceCancelFormValues,
} from "../model/occurrence-edit-schema";
import { useCancelCalendarOccurrence } from "../model/use-calendar-mutations";

export interface CancelOccurrenceFormProps {
  studioId: number;
  occurrence: OccurrenceResponse;
  onCancel: () => void;
  onCancelled: () => void;
}

export function CancelOccurrenceForm({
  studioId,
  occurrence,
  onCancel,
  onCancelled,
}: CancelOccurrenceFormProps) {
  const { cancelOccurrence, isCancelling } =
    useCancelCalendarOccurrence(studioId);
  const [values, setValues] = useState<OccurrenceCancelFormValues>({
    cancellation_reason: "",
  });
  const [errors, setErrors] = useState<
    Partial<Record<keyof OccurrenceCancelFormValues, string>>
  >({});

  return (
    <form
      className="mt-3 space-y-3 border-t border-neutral-200 pt-3"
      data-testid="cancel-occurrence-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseOccurrenceCancel(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        cancelOccurrence(
          { occurrenceId: occurrence.id, data: parsed.data },
          { onSuccess: onCancelled },
        );
      }}
    >
      <Textarea
        label="Cancellation reason"
        required
        rows={3}
        value={values.cancellation_reason}
        onChange={(event) =>
          setValues({ cancellation_reason: event.target.value })
        }
        error={errors.cancellation_reason}
        placeholder="e.g. Instructor unavailable — class moved to Thursday"
        data-testid="cancel-reason"
      />
      <p className="text-xs text-neutral-500">
        Customers with bookings will see this reason in their account.
      </p>
      <div className="flex justify-end gap-2">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isCancelling}
        >
          Keep session
        </Button>
        <Button type="submit" variant="danger" isLoading={isCancelling}>
          Cancel session
        </Button>
      </div>
    </form>
  );
}
