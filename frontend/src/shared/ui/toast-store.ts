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

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  push: (toast) => {
    const id = toast.id ?? crypto.randomUUID();
    set((state) => ({
      toasts: [...state.toasts, { ...toast, id }].slice(-MAX_TOASTS),
    }));
    return id;
  },
  dismiss: (id) =>
    set((state) => ({
      toasts: state.toasts.filter((item) => item.id !== id),
    })),
  clear: () => set({ toasts: [] }),
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
    globalThis.setTimeout(() => {
      useToastStore.getState().dismiss(id);
    }, duration);
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
