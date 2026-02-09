import React, { forwardRef } from "react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost";
  isLoading?: boolean;
  fullWidth?: boolean;
  asChild?: boolean;
}

const variantStyles = {
  primary:
    "bg-primary hover:bg-primary-dark text-white disabled:opacity-50 disabled:cursor-not-allowed",
  secondary:
    "border-2 border-neutral-300 text-neutral-700 hover:border-neutral-400 hover:bg-neutral-50",
  outline:
    "border-2 border-primary text-primary hover:bg-primary hover:text-white",
  ghost: "text-primary hover:text-primary-dark hover:bg-primary/10",
} as const;

const buttonClasses = (
  variant: ButtonProps["variant"],
  fullWidth: boolean,
  className: string
) => {
  const base =
    "font-semibold py-3 px-6 rounded-lg transition-colors duration-200 inline-flex items-center justify-center gap-2";
  return `${base} ${variantStyles[variant ?? "primary"]} ${fullWidth ? "w-full" : ""} ${className}`;
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
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
    const classNameMerged = buttonClasses(variant, fullWidth, className);

    if (asChild && React.isValidElement(children)) {
      return (
        <>
          {React.cloneElement(children as React.ReactElement<{ className?: string }>, {
            className: `${classNameMerged} ${(children as React.ReactElement<{ className?: string }>).props.className ?? ""}`.trim(),
          })}
        </>
      );
    }

    return (
      <button
        ref={ref}
        className={classNameMerged}
        disabled={disabled ?? isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin h-5 w-5"
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
            Loading...
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
