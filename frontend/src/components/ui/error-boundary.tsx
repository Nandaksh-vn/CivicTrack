import { Component, type ErrorInfo, type ReactNode } from "react";

import { ErrorState } from "@/components/ui/error-state";

export interface ErrorBoundaryProps {
  children: ReactNode;
  /** Optional test/debug hook; receives the render error. */
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/** Top-level render safety net; logs server-side via console in dev. */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    if (import.meta.env.DEV) {
      console.error("ErrorBoundary caught", error, info.componentStack);
    }
    this.props.onError?.(error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <ErrorState
          title="The application hit an unexpected error"
          message="Please reload the page. If it keeps happening, contact support."
          onRetry={() => window.location.reload()}
        />
      );
    }
    return this.props.children;
  }
}
