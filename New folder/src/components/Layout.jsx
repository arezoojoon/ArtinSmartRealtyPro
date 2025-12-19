import { Sidebar } from './Sidebar'
import { Header } from './Header'
import { useEffect, useState } from 'react'

export const Layout = ({ children }) => {
  const [isImpersonating, setIsImpersonating] = useState(false)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  useEffect(() => {
    // Check if in impersonation mode
    const checkImpersonation = () => {
      const impersonationData = sessionStorage.getItem('impersonating')
      setIsImpersonating(!!impersonationData)
    }

    checkImpersonation()
    // Listen for storage changes
    window.addEventListener('storage', checkImpersonation)
    
    return () => window.removeEventListener('storage', checkImpersonation)
  }, [])

  return (
    <div className="min-h-screen bg-navy-900 relative">
      {/* Background gradient */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-radial from-gold-500/3 via-transparent to-transparent"></div>
      </div>

      <Sidebar isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />
      <Header isSidebarOpen={isSidebarOpen} setIsSidebarOpen={setIsSidebarOpen} />

      {/* Mobile Sidebar Backdrop */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Main Content - Responsive margins */}
      <main className={`lg:ml-72 ${isImpersonating ? 'mt-32' : 'mt-20'} p-4 md:p-6 lg:p-8 relative z-10 transition-all duration-300`}>
        <div className="max-w-[1800px] mx-auto">
          {children}
        </div>
      </main>
    </div>
  )
}

export default Layout
