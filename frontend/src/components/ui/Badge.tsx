"use client";

import { forwardRef } from "react";

export type BadgeVariant =
  | "default"
  | "verified"
  | "new"
  | "available"
  | "booked"
  | "pending"
  | "popular";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  default: "bg-zinc-100 text-zinc-800",
  verified:
    "bg-linear-to-br from-sky-50 to-teal-50 text-teal-700 border border-teal-200",
  new: "bg-linear-to-br from-lime-50 to-yellow-50 text-lime-700 border border-lime-200",
  // Legacy (slot/booking)
  available:
    "inline-flex items-center gap-1 px-3 py-1 text-sm font-medium normal-case rounded-full bg-emerald-500 text-white",
  booked:
    "inline-flex items-center gap-1 px-3 py-1 text-sm font-medium normal-case rounded-full bg-zinc-200 text-zinc-700",
  pending:
    "inline-flex items-center gap-1 px-3 py-1 text-sm font-medium normal-case rounded-full bg-amber-100 text-amber-700",
  popular:
    "px-3 py-1 text-xs font-semibold rounded-full bg-teal-100 text-teal-700",
};

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "default", className = "", children, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={`${["default", "verified", "new", "popular"].includes(variant) ? "inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-wide" : ""} ${variantStyles[variant]} ${className}`}
        {...props}
      >
        {variant === "verified" && "✓ "}
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
