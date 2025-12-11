const LoadingSkeleton = ({ type = 'card', count = 1, className = '' }) => {
  const renderCardSkeleton = () => (
    <div className="bg-white/5 border border-white/10 rounded-xl p-6 animate-pulse">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="h-5 bg-white/10 rounded w-1/3"></div>
        <div className="h-4 bg-white/10 rounded w-16"></div>
      </div>

      {/* Content */}
      <div className="space-y-3">
        <div className="h-4 bg-white/10 rounded w-full"></div>
        <div className="h-4 bg-white/10 rounded w-5/6"></div>
        <div className="h-4 bg-white/10 rounded w-4/6"></div>
      </div>

      {/* Footer */}
      <div className="mt-4 pt-4 border-t border-white/5 flex gap-2">
        <div className="h-8 bg-white/10 rounded flex-1"></div>
        <div className="h-8 bg-white/10 rounded flex-1"></div>
      </div>
    </div>
  )

  const renderTableRowSkeleton = () => (
    <div className="flex items-center gap-4 py-4 border-b border-white/5 animate-pulse">
      <div className="w-10 h-10 bg-white/10 rounded-full"></div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-white/10 rounded w-1/4"></div>
        <div className="h-3 bg-white/10 rounded w-1/3"></div>
      </div>
      <div className="h-4 bg-white/10 rounded w-20"></div>
      <div className="h-4 bg-white/10 rounded w-24"></div>
    </div>
  )

  const renderStatSkeleton = () => (
    <div className="bg-white/5 border border-white/10 rounded-xl p-6 animate-pulse">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="h-4 bg-white/10 rounded w-24 mb-3"></div>
          <div className="h-8 bg-white/10 rounded w-20"></div>
        </div>
        <div className="w-12 h-12 bg-white/10 rounded-xl"></div>
      </div>
    </div>
  )

  const renderListItemSkeleton = () => (
    <div className="flex items-center gap-3 py-3 animate-pulse">
      <div className="w-8 h-8 bg-white/10 rounded-lg"></div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-white/10 rounded w-3/4"></div>
        <div className="h-3 bg-white/10 rounded w-1/2"></div>
      </div>
    </div>
  )

  const skeletons = {
    card: renderCardSkeleton,
    tableRow: renderTableRowSkeleton,
    stat: renderStatSkeleton,
    listItem: renderListItemSkeleton
  }

  const SkeletonComponent = skeletons[type] || renderCardSkeleton

  return (
    <div className={className}>
      {Array.from({ length: count }).map((_, index) => (
        <div key={index}>
          <SkeletonComponent />
        </div>
      ))}
    </div>
  )
}

export default LoadingSkeleton
