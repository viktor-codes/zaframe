import { forwardRef } from "react";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

export const Skeleton = forwardRef<HTMLDivElement, SkeletonProps>(
  ({ className = "", ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`animate-pulse bg-neutral-200 rounded ${className}`}
        aria-hidden
        {...props}
      />
    );
  }
);

Skeleton.displayName = "Skeleton";
