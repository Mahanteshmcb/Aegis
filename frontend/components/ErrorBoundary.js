import React from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * Global Error Boundary Component
 * Catches and displays errors gracefully without crashing the app
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error for debugging
    console.error('Error caught by boundary:', error, errorInfo);
    
    // Store error state
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Optional: Send error to monitoring service (Sentry, etc.)
    if (process.env.NODE_ENV === 'production') {
      // sendErrorToMonitoring(error, errorInfo);
    }
  }

  resetError = () => {
    this.setState({ 
      hasError: false, 
      error: null, 
      errorInfo: null 
    });
  };

  render() {
    if (this.state.hasError) {
      const isDev = process.env.NODE_ENV === 'development';

      return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-black flex items-center justify-center p-4">
          <div className="max-w-md w-full rounded-3xl border border-red-900/50 bg-slate-900/80 backdrop-blur p-8">
            <div className="flex items-center justify-center w-12 h-12 rounded-full bg-red-900/30 mx-auto mb-4">
              <AlertCircle className="text-red-400" size={24} />
            </div>

            <h1 className="text-2xl font-bold text-white text-center mb-2">
              Something went wrong
            </h1>

            <p className="text-slate-300 text-center text-sm mb-6">
              An unexpected error occurred. The team has been notified. Please try refreshing the page.
            </p>

            {isDev && this.state.error && (
              <div className="mb-6 p-3 rounded-lg bg-slate-950 border border-red-900/30 overflow-auto max-h-40">
                <p className="text-xs font-mono text-red-400">
                  {this.state.error.toString()}
                </p>
                {this.state.errorInfo && (
                  <p className="text-xs font-mono text-slate-400 mt-2 whitespace-pre-wrap">
                    {this.state.errorInfo.componentStack}
                  </p>
                )}
              </div>
            )}

            <div className="space-y-2">
              <button
                onClick={this.resetError}
                className="w-full px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-700 text-white font-semibold transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => window.location.href = '/estate-dashboard'}
                className="w-full px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold transition-colors"
              >
                Return to Estate Dashboard
              </button>
            </div>

            {isDev && (
              <p className="text-xs text-slate-500 text-center mt-4">
                Errors: {this.state.errorCount}
              </p>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Error handling utility functions
 */
export const handleError = (error, context = '') => {
  console.error(`Error in ${context}:`, error);
  
  // Return user-friendly error message
  if (error.response?.status === 401) {
    return 'Session expired. Please log in again.';
  }
  if (error.response?.status === 403) {
    return 'You do not have permission to perform this action.';
  }
  if (error.response?.status === 404) {
    return 'Resource not found.';
  }
  if (error.response?.status === 500) {
    return 'Server error. Please try again later.';
  }
  if (error.message === 'Network Error') {
    return 'Network error. Please check your connection.';
  }
  
  return error.message || 'An unexpected error occurred. Please try again.';
};

/**
 * Async error handler for API calls
 */
export const safeApiCall = async (apiFunction, defaultValue = null) => {
  try {
    return await apiFunction();
  } catch (error) {
    console.error('API Error:', error);
    return defaultValue;
  }
};

/**
 * Error notification component
 */
export function ErrorNotification({ error, onDismiss }) {
  if (!error) return null;

  return (
    <div className="fixed top-4 right-4 max-w-md p-4 rounded-lg bg-red-900/80 border border-red-700 backdrop-blur z-50 animate-slide-in">
      <div className="flex items-start gap-3">
        <AlertCircle className="text-red-400 flex-shrink-0 mt-0.5" size={20} />
        <div className="flex-1">
          <h3 className="font-semibold text-red-200">Error</h3>
          <p className="text-sm text-red-100 mt-1">{error}</p>
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className="text-red-400 hover:text-red-300 flex-shrink-0"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}

export default ErrorBoundary;
