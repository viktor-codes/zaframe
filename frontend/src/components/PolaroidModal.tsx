"use client";

import { useEffect } from "react";

export type PolaroidModalSize = "sm" | "md" | "lg" | "xl";

export interface PolaroidModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: React.ReactNode;
  children: React.ReactNode;
  size?: PolaroidModalSize;
}

const sizeClasses: Record<PolaroidModalSize, string> = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl",
  xl: "max-w-6xl",
};

export function PolaroidModal({
  isOpen,
  onClose,
  title,
  children,
  size = "md",
}: PolaroidModalProps) {
  useEffect(() => {
    if (!isOpen) return;
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handleEscape);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden
      />
      <div
        role="dialog"
        aria-modal
        aria-labelledby={title ? "polaroid-modal-title" : undefined}
        className={`relative w-full ${sizeClasses[size]} rounded-[32px] bg-white p-8 shadow-[0_60px_140px_rgba(16,17,20,0.35)] polaroid-modal-in`}
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-6 top-6 flex h-10 w-10 items-center justify-center rounded-full bg-zinc-100 text-zinc-600 transition hover:bg-zinc-200 hover:text-zinc-900"
          aria-label="Close"
        >
          ✕
        </button>
        {title != null && (
          <h2
            id="polaroid-modal-title"
            className="mb-6 text-2xl font-bold tracking-tight text-zinc-900"
          >
            {title}
          </h2>
        )}
        <div>{children}</div>
      </div>
    </div>
  );
}
