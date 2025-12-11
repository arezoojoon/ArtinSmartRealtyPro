const EmptyState = ({ 
  icon: Icon, 
  title, 
  description, 
  actionLabel, 
  onAction,
  className = '' 
}) => {
  return (
    <div className={`flex flex-col items-center justify-center py-16 px-4 ${className}`}>
      {/* Icon */}
      <div className="w-20 h-20 rounded-full bg-white/5 border-2 border-white/10 flex items-center justify-center mb-6">
        <Icon className="w-10 h-10 text-white/40" />
      </div>

      {/* Title */}
      <h3 className="text-xl font-semibold text-white mb-2">
        {title}
      </h3>

      {/* Description */}
      <p className="text-white/60 text-center max-w-md mb-8">
        {description}
      </p>

      {/* Action Button */}
      {actionLabel && onAction && (
        <button
          onClick={onAction}
          className="px-6 py-3 bg-gradient-to-r from-gold-600 to-gold-500 hover:from-gold-500 hover:to-gold-400 text-navy-900 font-semibold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-lg shadow-gold-500/20"
        >
          {actionLabel}
        </button>
      )}
    </div>
  )
}

export default EmptyState
