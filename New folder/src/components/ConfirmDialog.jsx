import { useState } from 'react'
import { X, AlertTriangle } from 'lucide-react'

const ConfirmDialog = ({ 
  isOpen, 
  onClose, 
  onConfirm, 
  title, 
  message, 
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  type = 'danger', // 'danger' | 'warning' | 'info'
  isLoading = false
}) => {
  if (!isOpen) return null

  const colors = {
    danger: {
      bg: 'bg-red-500/10',
      border: 'border-red-500/30',
      button: 'bg-red-500 hover:bg-red-600',
      icon: 'text-red-400'
    },
    warning: {
      bg: 'bg-yellow-500/10',
      border: 'border-yellow-500/30',
      button: 'bg-yellow-500 hover:bg-yellow-600',
      icon: 'text-yellow-400'
    },
    info: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/30',
      button: 'bg-blue-500 hover:bg-blue-600',
      icon: 'text-blue-400'
    }
  }

  const style = colors[type] || colors.danger

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-navy-800 border border-white/10 rounded-2xl shadow-2xl max-w-md w-full p-6 animate-scale-in">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-full ${style.bg} border ${style.border} flex items-center justify-center`}>
              <AlertTriangle className={`w-5 h-5 ${style.icon}`} />
            </div>
            <h3 className="text-xl font-semibold text-white">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/10 rounded-lg transition-colors"
            disabled={isLoading}
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Message */}
        <p className="text-white/70 mb-6 leading-relaxed">
          {message}
        </p>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 bg-white/5 hover:bg-white/10 text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            disabled={isLoading}
            className={`flex-1 px-4 py-2.5 ${style.button} text-white font-medium rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2`}
          >
            {isLoading && (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
            )}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

// Hook for easier usage
export const useConfirm = () => {
  const [confirmState, setConfirmState] = useState({
    isOpen: false,
    title: '',
    message: '',
    onConfirm: () => {},
    type: 'danger',
    confirmLabel: 'Confirm',
    cancelLabel: 'Cancel'
  })
  const [isLoading, setIsLoading] = useState(false)

  const confirm = ({ title, message, onConfirm, type, confirmLabel, cancelLabel }) => {
    return new Promise((resolve) => {
      setConfirmState({
        isOpen: true,
        title,
        message,
        onConfirm: async () => {
          setIsLoading(true)
          try {
            await onConfirm()
            resolve(true)
          } catch (error) {
            resolve(false)
          } finally {
            setIsLoading(false)
            setConfirmState(prev => ({ ...prev, isOpen: false }))
          }
        },
        type: type || 'danger',
        confirmLabel: confirmLabel || 'Confirm',
        cancelLabel: cancelLabel || 'Cancel'
      })
    })
  }

  const ConfirmDialogComponent = () => (
    <ConfirmDialog
      {...confirmState}
      isLoading={isLoading}
      onClose={() => setConfirmState(prev => ({ ...prev, isOpen: false }))}
    />
  )

  return { confirm, ConfirmDialog: ConfirmDialogComponent }
}

export default ConfirmDialog
