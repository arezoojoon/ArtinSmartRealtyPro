import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { toast } from 'react-toastify'
import { useEffect, useState } from 'react'

export const ProtectedRoute = ({ children, requiredRole = null }) => {
  const { isAuthenticated, isLoading, user } = useAuth()
  const [hasAccess, setHasAccess] = useState(true)

  useEffect(() => {
    if (!isLoading && isAuthenticated && requiredRole) {
      // Use user from AuthContext (Zustand) instead of localStorage
      // This prevents client-side role tampering
      if (user?.role !== requiredRole) {
        toast.error(`⛔ دسترسی محدود - فقط ${requiredRole}`)
        setHasAccess(false)
      }
    }
  }, [isLoading, isAuthenticated, requiredRole, user])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-navy-900">
        <div className="spinner"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (!hasAccess) {
    return <Navigate to="/" replace />
  }

  return children
}
