import { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw, Home } from 'lucide-react';
import { Button } from './Button';

export interface RouteErrorBoundaryProps {
  children: ReactNode;
  fallbackTitle?: string;
  onReset?: () => void;
}

export interface RouteErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  isChunkLoadError: boolean;
}

const CHUNK_RETRY_KEY = 'gqt_chunk_retry_timestamp';
const RETRY_COOLDOWN_MS = 15000; // 15 seconds cooldown to prevent reload loops

export class RouteErrorBoundary extends Component<RouteErrorBoundaryProps, RouteErrorBoundaryState> {
  public state: RouteErrorBoundaryState = {
    hasError: false,
    error: null,
    isChunkLoadError: false,
  };

  public static getDerivedStateFromError(error: Error): RouteErrorBoundaryState {
    const message = (error?.message || '').toLowerCase();
    const name = (error?.name || '').toLowerCase();
    const isChunkLoadError =
      name.includes('chunkloaderror') ||
      message.includes('loading chunk') ||
      message.includes('failed to fetch dynamically imported module') ||
      message.includes('importing a module script failed') ||
      message.includes('error loading dynamically imported module');

    return {
      hasError: true,
      error,
      isChunkLoadError,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    if (process.env.NODE_ENV !== 'production') {
      console.error('[RouteErrorBoundary caught error]:', error, errorInfo);
    }

    // Auto-reload once if chunk load error occurred outside cooldown window
    if (this.state.isChunkLoadError && typeof window !== 'undefined') {
      const lastRetry = sessionStorage.getItem(CHUNK_RETRY_KEY);
      const now = Date.now();
      if (!lastRetry || now - parseInt(lastRetry, 10) > RETRY_COOLDOWN_MS) {
        sessionStorage.setItem(CHUNK_RETRY_KEY, now.toString());
        window.location.reload();
      }
    }
  }

  private handleRetry = () => {
    if (typeof window !== 'undefined') {
      if (this.state.isChunkLoadError) {
        window.location.reload();
        return;
      }
      this.setState({ hasError: false, error: null, isChunkLoadError: false });
      if (this.props.onReset) {
        this.props.onReset();
      }
    }
  };

  private handleGoHome = () => {
    if (typeof window !== 'undefined') {
      window.location.href = '/';
    }
  };

  public render() {
    if (this.state.hasError) {
      const isChunk = this.state.isChunkLoadError;
      return (
        <div
          role="alert"
          aria-live="assertive"
          className="min-h-[340px] flex items-center justify-center p-6"
        >
          <div className="w-full max-w-lg bg-white rounded-2xl border border-rose-200/80 shadow-sm p-8 text-center space-y-5">
            <div className="w-14 h-14 bg-rose-50 rounded-2xl flex items-center justify-center mx-auto text-rose-600 ring-8 ring-rose-50/50">
              <AlertCircle className="w-7 h-7" />
            </div>

            <div className="space-y-2">
              <h3 className="text-lg font-bold text-gqt-navy-900 tracking-tight">
                {isChunk
                  ? 'Application Update Detected'
                  : (this.props.fallbackTitle || 'Unable to Load View')}
              </h3>
              <p className="text-sm text-gqt-neutral-600 leading-relaxed max-w-md mx-auto">
                {isChunk
                  ? 'A new version of GQT HRMS has been deployed or your network connection was interrupted. Please reload the page to load the latest application assets.'
                  : 'An unexpected error occurred while rendering this view. Your session and data are secure. Please try reloading or returning to the dashboard.'}
              </p>
            </div>

            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Button
                variant="primary"
                onClick={this.handleRetry}
                className="w-full sm:w-auto inline-flex items-center justify-center"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                {isChunk ? 'Reload Application' : 'Try Again'}
              </Button>
              <Button
                variant="outline"
                onClick={this.handleGoHome}
                className="w-full sm:w-auto inline-flex items-center justify-center border-gqt-neutral-300 text-gqt-neutral-700 hover:bg-gqt-neutral-50"
              >
                <Home className="w-4 h-4 mr-2" />
                Return to Dashboard
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
