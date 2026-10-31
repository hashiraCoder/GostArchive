import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onReset?: () => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("Uncaught frontend error in component tree:", error, errorInfo);
  }

  private handleReset = (): void => {
    this.setState({ hasError: false, error: null });
    this.props.onReset?.();
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          role="alert"
          className="m-6 p-6 rounded-lg border border-red-300 bg-red-50/80 text-red-900 shadow-sm max-w-2xl mx-auto space-y-4"
        >
          <div className="flex items-center gap-2">
            <span className="font-bold text-xs tracking-wide uppercase bg-red-200/60 px-2 py-0.5 rounded text-red-950">
              Rendering Error
            </span>
          </div>
          <div>
            <h3 className="font-serif font-bold text-base text-red-950">
              Something went wrong in the workspace UI
            </h3>
            <p className="mt-1 text-xs text-red-800 leading-relaxed">
              {this.state.error?.message || "An unexpected error occurred while rendering this view."}
            </p>
          </div>
          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={this.handleReset}
              className="px-3.5 py-1.5 text-xs font-semibold bg-red-800 text-white rounded hover:bg-red-900 transition shadow-sm"
            >
              Try Again
            </button>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-3.5 py-1.5 text-xs font-semibold bg-white border border-red-300 text-red-800 rounded hover:bg-red-50 transition"
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
