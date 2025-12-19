/**
 * Impersonation Banner - Shows when Super Admin is viewing a tenant's dashboard
 * Sticky top banner with exit option
 */
import React from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, AlertTriangle } from 'lucide-react'

const ImpersonationBanner = () => {
  const navigate = useNavigate()
  const impersonationData = JSON.parse(sessionStorage.getItem('impersonating') || 'null')

  if (!impersonationData) return null

  const handleExit = () => {
    // Restore original super admin token
    const fallbackToken = sessionStorage.getItem('admin_fallback_token')
    
    if (fallbackToken) {
      localStorage.setItem('auth-storage', fallbackToken)
    }

    // Clear impersonation data
    sessionStorage.removeItem('impersonating')
    sessionStorage.removeItem('admin_fallback_token')

    // Redirect to super admin dashboard
    window.location.href = '/superadmin'
  }

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-gradient-to-r from-amber-500 via-amber-600 to-amber-500 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-white animate-pulse" />
            <div>
              <p className="text-white font-semibold">
                ⚠️ Impersonation Mode Active
              </p>
              <p className="text-amber-100 text-sm">
                You are viewing <span className="font-bold">{impersonationData.tenantName}</span>'s dashboard
              </p>
            </div>
          </div>
          <button
            onClick={handleExit}
            className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg transition-all duration-200 border border-white/30 hover:border-white/50 font-medium"
          >
            <LogOut className="w-4 h-4" />
            Exit to Super Admin
          </button>
        </div>
      </div>
    </div>
  )
}

export default ImpersonationBanner
