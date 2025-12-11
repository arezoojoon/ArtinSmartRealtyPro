import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('❌ Error caught by boundary:', error, errorInfo);
    this.setState({ error, errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gradient-to-br from-navy-900 via-navy-800 to-navy-900 flex items-center justify-center p-4">
          <div className="glass-card p-8 max-w-lg w-full text-center">
            <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            
            <h2 className="text-2xl font-bold text-white mb-2">Unexpected Error</h2>
            <p className="text-gray-400 mb-6">Something went wrong. Please refresh the page.</p>
            
            {this.state.error && (
              <details className="text-left bg-navy-900/50 p-4 rounded-lg mb-6">
                <summary className="text-gold-500 cursor-pointer mb-2 font-semibold">Error Details</summary>
                <pre className="text-xs text-red-400 overflow-auto max-h-40">
                  {typeof this.state.error === 'object' 
                    ? JSON.stringify(this.state.error, null, 2)
                    : String(this.state.error)}
                </pre>
              </details>
            )}
            
            <button
              onClick={() => window.location.reload()}
              className="btn-gold px-6 py-3 rounded-lg font-semibold"
            >
              Refresh Page
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
