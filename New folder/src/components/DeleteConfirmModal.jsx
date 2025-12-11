import { AlertTriangle, Trash2, X } from 'lucide-react'

const DeleteConfirmModal = ({ isOpen, onClose, onConfirm, leadName, isDeleting }) => {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="glass-card rounded-2xl max-w-md w-full shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-red-500/20 rounded-xl flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-red-400" />
            </div>
            <h2 className="text-xl font-bold text-white">Delete Lead</h2>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-white/10 rounded-lg transition-colors"
            disabled={isDeleting}
          >
            <X className="w-5 h-5 text-white/60" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-white/70 mb-2">
            Are you sure you want to delete this lead?
          </p>
          <p className="text-white font-semibold mb-4">
            {leadName}
          </p>
          <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl">
            <p className="text-sm text-red-300">
              ⚠️ This action cannot be undone. All data associated with this lead will be permanently deleted.
            </p>
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center gap-4 p-6 border-t border-white/10">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 bg-white/5 hover:bg-white/10 border border-white/10 rounded-xl text-white font-medium transition-all"
            disabled={isDeleting}
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={isDeleting}
            className="flex-1 px-6 py-3 bg-gradient-to-br from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 rounded-xl text-white font-bold transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isDeleting ? (
              <>
                <div className="spinner w-5 h-5 border-2"></div>
                <span>Deleting...</span>
              </>
            ) : (
              <>
                <Trash2 className="w-5 h-5" />
                <span>Delete Lead</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default DeleteConfirmModal
