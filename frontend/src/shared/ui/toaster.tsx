"use client";

/**
 * Renders the global toast stack. Mount once in app providers.
 */

import { AnimatePresence, motion } from "framer-motion";
import { X } from "lucide-react";

import { toast, useToastStore, type ToastTone } from "./toast-store";

const toneStyles: Record<ToastTone, string> = {
  error: "border-red-200 bg-red-50 text-red-900",
  success: "border-green-200 bg-green-50 text-green-900",
  info: "border-neutral-200 bg-white text-neutral-900",
};

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);

  return (
    <div
      className="pointer-events-none fixed inset-x-0 bottom-0 z-50 flex flex-col items-center gap-2 p-4 sm:items-end"
      aria-live="polite"
      aria-relevant="additions"
    >
      <AnimatePresence initial={false}>
        {toasts.map((item) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0, y: 12, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className={`pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border px-4 py-3 shadow-sm ${toneStyles[item.tone]}`}
            role={item.tone === "error" ? "alert" : "status"}
          >
            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">{item.message}</p>
              {item.requestId ? (
                <p className="mt-1 truncate font-mono text-xs opacity-70">
                  Ref: {item.requestId}
                </p>
              ) : null}
            </div>
            <button
              type="button"
              className="shrink-0 rounded-md p-1 opacity-70 hover:opacity-100"
              aria-label="Dismiss notification"
              onClick={() => toast.dismiss(item.id)}
            >
              <X className="h-4 w-4" aria-hidden />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}
