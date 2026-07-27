/**
 * Imperative toast API for transient feedback (errors, success).
 * UI lives in `Toaster` — mount once under app providers.
 */

import { create } from "zustand";

export type ToastTone = "error" | "success" | "info";

export interface ToastItem {
  id: string;
  message: string;
  tone: ToastTone;
  /** Optional correlation id for support (shown only in dev-friendly detail). */
  requestId?: string;
}

interface ToastState {
  toasts: ToastItem[];
  push: (toast: Omit<ToastItem, "id"> & { id?: string }) => string;
  dismiss: (id: string) => void;
  clear: () => void;
}

const MAX_TOASTS = 3;
const DEFAULT_DURATION_MS = 5_000;
const dismissTimers = new Map<string, ReturnType<typeof setTimeout>>();

function clearDismissTimer(id: string): void {
  const timer = dismissTimers.get(id);
  if (timer !== undefined) {
    globalThis.clearTimeout(timer);
    dismissTimers.delete(id);
  }
}

export const useToastStore = create<ToastState>((set, get) => ({
  toasts: [],
  push: (toast) => {
    const id = toast.id ?? crypto.randomUUID();
    const previous = get().toasts;
    const next = [...previous, { ...toast, id }];
    const sliced = next.slice(-MAX_TOASTS);
    for (const item of previous) {
      if (!sliced.some((kept) => kept.id === item.id)) {
        clearDismissTimer(item.id);
      }
    }
    set({ toasts: sliced });
    return id;
  },
  dismiss: (id) => {
    clearDismissTimer(id);
    set((state) => ({
      toasts: state.toasts.filter((item) => item.id !== id),
    }));
  },
  clear: () => {
    for (const id of [...dismissTimers.keys()]) {
      clearDismissTimer(id);
    }
    set({ toasts: [] });
  },
}));

function show(
  tone: ToastTone,
  message: string,
  options?: { requestId?: string; durationMs?: number },
): string {
  const id = useToastStore.getState().push({
    tone,
    message,
    requestId: options?.requestId,
  });
  const duration = options?.durationMs ?? DEFAULT_DURATION_MS;
  if (duration > 0) {
    clearDismissTimer(id);
    const timer = globalThis.setTimeout(() => {
      useToastStore.getState().dismiss(id);
    }, duration);
    dismissTimers.set(id, timer);
  }
  return id;
}

export const toast = {
  error: (message: string, options?: { requestId?: string; durationMs?: number }) =>
    show("error", message, options),
  success: (
    message: string,
    options?: { requestId?: string; durationMs?: number },
  ) => show("success", message, options),
  info: (message: string, options?: { requestId?: string; durationMs?: number }) =>
    show("info", message, options),
  dismiss: (id: string) => useToastStore.getState().dismiss(id),
};
