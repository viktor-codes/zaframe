import { forwardRef } from "react";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "interactive" | "disabled";
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ variant = "default", className = "", ...props }, ref) => {
    const base = "polaroid-card";

    const variantStyles = {
      default: "",
      interactive:
        "hover:shadow-2xl transition-shadow duration-300 cursor-pointer",
      disabled: "opacity-50 cursor-not-allowed",
    } as const;

    return (
      <div
        ref={ref}
        className={`${base} ${variantStyles[variant]} ${className}`}
        {...props}
      />
    );
  }
);

Card.displayName = "Card";
