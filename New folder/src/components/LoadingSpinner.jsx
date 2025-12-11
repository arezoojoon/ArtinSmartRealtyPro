const LoadingSpinner = ({ 
  size = 'md', 
  color = 'gold',
  text,
  className = '' 
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  }

  const colors = {
    gold: 'border-gold-500',
    white: 'border-white',
    blue: 'border-blue-500',
    green: 'border-green-500',
    red: 'border-red-500'
  }

  return (
    <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
      <div className={`${sizes[size]} border-4 ${colors[color]}/30 border-t-${colors[color].replace('border-', '')} rounded-full animate-spin`}></div>
      {text && (
        <p className="text-white/60 text-sm animate-pulse">{text}</p>
      )}
    </div>
  )
}

export default LoadingSpinner
