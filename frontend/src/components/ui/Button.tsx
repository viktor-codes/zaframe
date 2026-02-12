"use client";

import React, { forwardRef } from "react";

export type ButtonSize = "sm" | "md" | "lg";
export type ButtonVariant = "primary" | "secondary" | "outline" | "ghost" | "danger";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  fullWidth?: boolean;
  /** Рендерить как дочерний элемент (например Link), передавая стили и пропсы */
  asChild?: boolean;
}

const base =
  "inline-flex items-center justify-center rounded-full font-semibold transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-linear-to-br from-sky-400 via-teal-400 to-lime-300 text-zinc-900 shadow-sm hover:shadow-md hover:brightness-[1.03]",
  secondary:
    "bg-white text-zinc-900 border-2 border-zinc-200 hover:bg-zinc-50 hover:border-zinc-300",
  outline:
    "border-2 border-teal-400 text-teal-600 hover:bg-teal-50 hover:border-teal-500",
  ghost: "bg-transparent text-zinc-800 hover:bg-zinc-100 active:bg-zinc-200",
  danger: "bg-red-500 text-white hover:bg-red-600 shadow-sm hover:shadow-md",
};

const sizes: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-4 py-2 text-sm",
  lg: "px-6 py-3 text-base",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      fullWidth = false,
      asChild = false,
      className = "",
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const classes = [
      base,
      variants[variant],
      sizes[size],
      fullWidth ? "w-full" : "",
      className,
    ]
      .filter(Boolean)
      .join(" ");

    if (asChild && React.isValidElement(children)) {
      const child = children as React.ReactElement<{ className?: string }>;
      return React.cloneElement(child, {
        ...child.props,
        ...props,
        className: [classes, child.props.className].filter(Boolean).join(" "),
      });
    }

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled ?? isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <svg
              className="h-5 w-5 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            <span className="ml-2">Loading...</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
