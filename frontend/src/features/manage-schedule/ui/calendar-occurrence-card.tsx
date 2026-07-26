"use client";

import { useState } from "react";

import {
  isOccurrenceCancelled,
  isOccurrenceScheduled,
  type OccurrenceResponse,
} from "@entities/occurrence";
import { Button, Chip } from "@shared/ui";

import { formatOccurrenceTimeRange } from "../model/datetime-local";
import { CancelOccurrenceForm } from "./cancel-occurrence-form";
import { EditOccurrenceForm } from "./edit-occurrence-form";

export interface CalendarOccurrenceCardProps {
  studioId: number;
  occurrence: OccurrenceResponse;
}

type PanelMode = "idle" | "edit" | "cancel";

function statusTone(
  status: OccurrenceResponse["status"],
): "neutral" | "success" | "warning" {
  if (status === "scheduled") return "success";
  if (status === "cancelled") return "warning";
  return "neutral";
}

export function CalendarOccurrenceCard({
  studioId,
  occurrence,
}: CalendarOccurrenceCardProps) {
  const [mode, setMode] = useState<PanelMode>("idle");
  const canManage = isOccurrenceScheduled(occurrence);

  return (
    <article
      className="rounded-xl border border-neutral-200 bg-white px-4 py-3"
      data-testid={`calendar-occurrence-${occurrence.id}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-display text-base font-semibold text-neutral-900">
              {occurrence.title}
            </h3>
            <Chip tone={statusTone(occurrence.status)} size="sm">
              {occurrence.status}
            </Chip>
          </div>
          <p className="text-sm text-neutral-600">
            {formatOccurrenceTimeRange(
              occurrence.start_time,
              occurrence.end_time,
            )}
            <span className="text-neutral-400">
              {" "}
              · capacity {occurrence.max_capacity}
            </span>
          </p>
          {isOccurrenceCancelled(occurrence) &&
          occurrence.cancellation_reason ? (
            <p className="text-xs text-amber-800">
              Reason: {occurrence.cancellation_reason}
            </p>
          ) : null}
        </div>

        {canManage ? (
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setMode((current) => (current === "edit" ? "idle" : "edit"))
              }
            >
              Edit
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                setMode((current) =>
                  current === "cancel" ? "idle" : "cancel",
                )
              }
            >
              Cancel
            </Button>
          </div>
        ) : null}
      </div>

      {mode === "edit" ? (
        <EditOccurrenceForm
          studioId={studioId}
          occurrence={occurrence}
          onCancel={() => setMode("idle")}
          onSaved={() => setMode("idle")}
        />
      ) : null}

      {mode === "cancel" ? (
        <CancelOccurrenceForm
          studioId={studioId}
          occurrence={occurrence}
          onCancel={() => setMode("idle")}
          onCancelled={() => setMode("idle")}
        />
      ) : null}
    </article>
  );
}
