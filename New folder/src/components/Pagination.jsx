import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'
import { useLanguage } from '../context/LanguageContext'

const Pagination = ({ 
  currentPage, 
  totalPages, 
  onPageChange,
  itemsPerPage,
  totalItems 
}) => {
  const { t } = useLanguage()
  
  const pages = []
  const maxPagesToShow = 5
  
  // Calculate page range to show
  let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2))
  let endPage = Math.min(totalPages, startPage + maxPagesToShow - 1)
  
  if (endPage - startPage < maxPagesToShow - 1) {
    startPage = Math.max(1, endPage - maxPagesToShow + 1)
  }
  
  for (let i = startPage; i <= endPage; i++) {
    pages.push(i)
  }

  if (totalPages === 0) return null

  const startItem = ((currentPage - 1) * itemsPerPage) + 1
  const endItem = Math.min(currentPage * itemsPerPage, totalItems)

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 mt-6 px-4 py-3 bg-white/5 rounded-xl border border-white/10">
      {/* Items info */}
      <div className="text-sm text-white/60">
        {t('showing')} <span className="font-semibold text-white number">{startItem}</span> {t('to')}{' '}
        <span className="font-semibold text-white number">{endItem}</span> {t('of')}{' '}
        <span className="font-semibold text-white number">{totalItems}</span> {t('results')}
      </div>

      {/* Pagination controls */}
      <div className="flex items-center gap-2">
        {/* First page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all touch-manipulation"
          aria-label={t('firstPage')}
        >
          <ChevronsLeft className="w-4 h-4 text-white/70" />
        </button>

        {/* Previous page */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all touch-manipulation"
          aria-label={t('previousPage')}
        >
          <ChevronLeft className="w-4 h-4 text-white/70" />
        </button>

        {/* Page numbers */}
        <div className="hidden sm:flex items-center gap-1">
          {startPage > 1 && (
            <>
              <button
                onClick={() => onPageChange(1)}
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 text-sm font-medium transition-all"
              >
                1
              </button>
              {startPage > 2 && (
                <span className="px-2 text-white/40">...</span>
              )}
            </>
          )}

          {pages.map(page => (
            <button
              key={page}
              onClick={() => onPageChange(page)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-all touch-manipulation ${
                page === currentPage
                  ? 'bg-gold-500 text-navy-900'
                  : 'bg-white/5 hover:bg-white/10 text-white/70'
              }`}
            >
              {page}
            </button>
          ))}

          {endPage < totalPages && (
            <>
              {endPage < totalPages - 1 && (
                <span className="px-2 text-white/40">...</span>
              )}
              <button
                onClick={() => onPageChange(totalPages)}
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-white/70 text-sm font-medium transition-all"
              >
                {totalPages}
              </button>
            </>
          )}
        </div>

        {/* Mobile: Just show current page */}
        <div className="sm:hidden px-4 py-2 bg-white/5 rounded-lg">
          <span className="text-sm font-medium text-white number">
            {currentPage} / {totalPages}
          </span>
        </div>

        {/* Next page */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all touch-manipulation"
          aria-label={t('nextPage')}
        >
          <ChevronRight className="w-4 h-4 text-white/70" />
        </button>

        {/* Last page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={currentPage === totalPages}
          className="p-2 rounded-lg bg-white/5 hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-all touch-manipulation"
          aria-label={t('lastPage')}
        >
          <ChevronsRight className="w-4 h-4 text-white/70" />
        </button>
      </div>
    </div>
  )
}

export default Pagination
