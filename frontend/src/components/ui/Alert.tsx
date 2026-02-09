import { forwardRef } from "react";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "success" | "error" | "info";
  title?: string;
}

const variantStyles = {
  success: "border-l-4 border-primary",
  error: "border-l-4 border-red-500",
  info: "border-l-4 border-blue-500",
} as const;

const variantIcons = {
  success: (
    <svg
      className="w-6 h-6 text-primary flex-shrink-0"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
        clipRule="evenodd"
      />
    </svg>
  ),
  error: (
    <svg
      className="w-6 h-6 text-red-500 flex-shrink-0"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  ),
  info: (
    <svg
      className="w-6 h-6 text-blue-500 flex-shrink-0"
      fill="currentColor"
      viewBox="0 0 20 20"
      aria-hidden
    >
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
        clipRule="evenodd"
      />
    </svg>
  ),
} as const;

export const Alert = forwardRef<HTMLDivElement, AlertProps>(
  (
    {
      variant = "info",
      title,
      className = "",
      children,
      role = "alert",
      ...props
    },
    ref
  ) => {
    return (
      <div
        ref={ref}
        className={`polaroid-card ${variantStyles[variant]} ${className}`}
        role={role}
        {...props}
      >
        <div className="flex gap-3">
          {variantIcons[variant]}
          <div>
            {title && (
              <h4 className="font-semibold text-secondary">{title}</h4>
            )}
            <div className="text-sm text-neutral-600">{children}</div>
          </div>
        </div>
      </div>
    );
  }
);

Alert.displayName = "Alert";
