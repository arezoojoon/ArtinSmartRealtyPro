import { AlertCircle, RefreshCw } from 'lucide-react'

const ErrorState = ({ 
  title = 'Something went wrong',
  message = 'An error occurred while loading the data.',
  onRetry,
  retryLabel = 'Try Again',
  error
}) => {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Error Icon */}
      <div className="w-20 h-20 rounded-full bg-red-500/10 border-2 border-red-500/30 flex items-center justify-center mb-6">
        <AlertCircle className="w-10 h-10 text-red-400" />
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-white mb-2">
        {title}
      </h3>

      {/* Message */}
      <p className="text-white/60 text-center max-w-md mb-2">
        {message}
      </p>

      {/* Error Details (Development) */}
      {error && process.env.NODE_ENV === 'development' && (
        <details className="mt-4 mb-4 max-w-lg">
          <summary className="text-sm text-white/40 cursor-pointer hover:text-white/60 transition-colors">
            Error Details
          </summary>
          <pre className="mt-2 p-3 bg-black/30 rounded-lg text-xs text-red-300 overflow-auto max-h-32">
            {error.toString()}
            {error.stack && `\n\n${error.stack}`}
          </pre>
        </details>
      )}

      {/* Retry Button */}
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-4 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-medium rounded-xl transition-all flex items-center gap-2 group"
        >
          <RefreshCw className="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" />
          {retryLabel}
        </button>
      )}
    </div>
  )
}

export default ErrorState
