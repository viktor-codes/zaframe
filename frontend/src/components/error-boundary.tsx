"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui";

export interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional custom fallback UI */
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
}

/**
 * Catches render errors in child trees. Use around major feature sections.
 */
export class ErrorBoundary extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  state: ErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(_error: Error, _info: ErrorInfo): void {
    void _error;
    void _info;
    // Hook for client-side error reporting (e.g. Sentry) when added.
  }

  private handleReset = (): void => {
    this.setState({ hasError: false });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div
          className="min-h-[200px] rounded-xl border border-neutral-200 bg-neutral-50 p-8 text-center"
          role="alert"
        >
          <p className="text-secondary font-semibold">Something went wrong</p>
          <p className="mt-2 text-sm text-neutral-600">
            This section could not be displayed. You can try again or reload the
            page.
          </p>
          <Button type="button" className="mt-6" onClick={this.handleReset}>
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
