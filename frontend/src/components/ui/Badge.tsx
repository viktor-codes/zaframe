import { forwardRef } from "react";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "available" | "booked" | "pending" | "new" | "popular";
}

const variantStyles = {
  available:
    "inline-flex items-center gap-1 px-3 py-1 bg-primary text-white text-sm font-medium rounded-full",
  booked:
    "inline-flex items-center gap-1 px-3 py-1 bg-neutral-200 text-neutral-700 text-sm font-medium rounded-full",
  pending:
    "inline-flex items-center gap-1 px-3 py-1 bg-amber-100 text-amber-700 text-sm font-medium rounded-full",
  new: "px-3 py-1 bg-secondary text-white text-xs font-semibold rounded-full",
  popular:
    "px-3 py-1 bg-primary/10 text-primary text-xs font-semibold rounded-full",
} as const;

const variantIcons = {
  available: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  ),
  booked: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  ),
  pending: (
    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20" aria-hidden>
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
        clipRule="evenodd"
      />
    </svg>
  ),
  new: null,
  popular: null,
} as const;

export const Badge = forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "available", className = "", children, ...props }, ref) => {
    const icon = variantIcons[variant];

    return (
      <span
        ref={ref}
        className={`${variantStyles[variant]} ${className}`}
        {...props}
      >
        {icon}
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";
