"use client";

export interface BookingSummaryCardProps {
  studio: string;
  classType: string;
  date: string;
  time: string;
  price: string;
  credits?: boolean;
}

export function BookingSummaryCard({
  studio,
  classType,
  date,
  time,
  price,
  credits = false,
}: BookingSummaryCardProps) {
  return (
    <div className="rounded-2xl border-2 border-zinc-200 bg-zinc-50 p-6">
      <div className="mb-4 text-sm font-semibold uppercase tracking-wide text-zinc-500">
        Booking Summary
      </div>

      <div className="space-y-3">
        <div>
          <div className="text-xs text-zinc-500">Studio</div>
          <div className="font-semibold text-zinc-900">{studio}</div>
        </div>

        <div>
          <div className="text-xs text-zinc-500">Class</div>
          <div className="font-semibold text-zinc-900">{classType}</div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <div className="text-xs text-zinc-500">Date</div>
            <div className="font-semibold text-zinc-900">{date}</div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Time</div>
            <div className="font-semibold text-zinc-900">{time}</div>
          </div>
        </div>
      </div>

      <div className="my-4 border-t border-zinc-300" />

      <div className="flex items-center justify-between">
        <div className="text-sm text-zinc-600">Total</div>
        <div className="text-xl font-bold text-zinc-900">{price}</div>
      </div>

      {credits && (
        <div className="mt-2 rounded-lg bg-gradient-to-br from-sky-50 to-teal-50 p-3 text-xs">
          <span className="font-semibold text-teal-700">
            💎 Use 1 credit instead
          </span>
        </div>
      )}
    </div>
  );
}
