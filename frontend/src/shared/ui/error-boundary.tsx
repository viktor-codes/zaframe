"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

import { Button } from "./button";

export interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback UI */
  fallback?: ReactNode;
  /** Shown in the default fallback heading */
  title?: string;
  /** Shown under the title in the default fallback */
  description?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Catches render errors in child trees. Use around major route groups / features.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Hook for client-side error reporting (e.g. Sentry) when added.
    if (process.env.NODE_ENV !== "production") {
      console.error("[ErrorBoundary]", error, info.componentStack);
    }
  }

  private handleReset = (): void => {
    this.setState({ hasError: false });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      const title = this.props.title ?? "Something went wrong";
      const description =
        this.props.description ??
        "This section could not be displayed. You can try again or reload the page.";
      return (
        <div
          className="min-h-[200px] rounded-xl border border-neutral-200 bg-neutral-50 p-8 text-center"
          role="alert"
        >
          <p className="text-secondary font-semibold">{title}</p>
          <p className="mt-2 text-sm text-neutral-600">{description}</p>
          <Button type="button" className="mt-6" onClick={this.handleReset}>
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
