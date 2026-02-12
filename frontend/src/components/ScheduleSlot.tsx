"use client";

import { Button } from "./ui/Button";
import { Chip } from "./ui/Chip";

export interface ScheduleSlotProps {
  time: string;
  title: string;
  instructor: string;
  duration: string;
  price: string;
  spotsLeft: number;
  onBook?: () => void;
}

export function ScheduleSlot({
  time,
  title,
  instructor,
  duration,
  price,
  spotsLeft,
  onBook,
}: ScheduleSlotProps) {
  return (
    <div className="group flex items-center justify-between rounded-2xl border border-zinc-200 bg-white p-4 transition hover:border-teal-300 hover:bg-teal-50/30">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <div className="text-lg font-bold text-zinc-900">{time}</div>
          <div className="h-4 w-px bg-zinc-300" aria-hidden />
          <div className="font-semibold text-zinc-800">{title}</div>
          {spotsLeft <= 5 && (
            <Chip tone="warning" size="xs">
              {spotsLeft} left
            </Chip>
          )}
        </div>
        <div className="mt-1 flex items-center gap-4 text-xs text-zinc-600">
          <span>{instructor}</span>
          <span>•</span>
          <span>{duration}</span>
          <span>•</span>
          <span className="font-semibold text-zinc-900">{price}</span>
        </div>
      </div>
      <Button size="sm" onClick={onBook}>
        Book
      </Button>
    </div>
  );
}
