"use client";

import { useEffect, useState } from "react";

export interface UseNowOptions {
  /** Tick interval in ms. Default 1000. */
  intervalMs?: number;
  /** When false, clock freezes after the last tick (or initial mount). */
  enabled?: boolean;
}

/**
 * Client clock that advances on an interval.
 * Use for hold countdowns, cancel cutoffs, and time-bucketed lists.
 */
export function useNow(options: UseNowOptions = {}): Date {
  const { intervalMs = 1000, enabled = true } = options;
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    if (!enabled) return;

    // WHY: avoid synchronous setState in the effect body (react-hooks/set-state-in-effect).
    // Initial state already seeds `now`; interval keeps the clock fresh while enabled.
    const id = window.setInterval(() => setNow(new Date()), intervalMs);
    return () => window.clearInterval(id);
  }, [enabled, intervalMs]);

  return now;
}
