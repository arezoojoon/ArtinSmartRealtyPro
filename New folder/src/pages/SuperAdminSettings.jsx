import { useState } from 'react'
import { Layout } from '../components/Layout'
import { Settings, Lock, User, Mail, CheckCircle, AlertCircle } from 'lucide-react'
import { api, useAuth } from '../context/AuthContext'

const SuperAdminSettings = () => {
  const { user } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    // Validation
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setError('New passwords do not match')
      setIsLoading(false)
      return
    }

    if (passwordData.newPassword.length < 6) {
      setError('Password must be at least 6 characters')
      setIsLoading(false)
      return
    }

    try {
      await api.post('/api/auth/change-password', {
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword
      })

      setSuccess('Password changed successfully!')
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to change password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Layout>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <Settings className="w-8 h-8 text-gold-500" />
            Super Admin Settings
          </h1>
          <p className="text-gray-400">
            Manage your account settings and security
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Info */}
          <div className="glass-card rounded-2xl p-6">
            <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
              <User className="w-5 h-5 text-gold-500" />
              Profile Information
            </h2>
            <div className="space-y-4">
              <div>
                <label className="text-sm text-white/50 block mb-1">Username</label>
                <div className="text-white font-medium">{user?.username}</div>
              </div>
              <div>
                <label className="text-sm text-white/50 block mb-1">Email</label>
                <div className="text-white font-medium flex items-center gap-2">
                  <Mail className="w-4 h-4 text-gold-500" />
                  {user?.email || 'admin@artinsmartagent.com'}
                </div>
              </div>
              <div>
                <label className="text-sm text-white/50 block mb-1">Role</label>
                <div className="inline-flex items-center gap-2 px-3 py-1 bg-gold-500/20 text-gold-400 rounded-lg text-sm font-medium">
                  🔐 Super Administrator
                </div>
              </div>
            </div>
          </div>

          {/* Change Password */}
          <div className="lg:col-span-2 glass-card rounded-2xl p-6">
            <h2 className="text-xl font-bold text-white mb-6 flex items-center gap-2">
              <Lock className="w-5 h-5 text-gold-500" />
              Change Password
            </h2>

            {/* Success Message */}
            {success && (
              <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-xl flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-green-300">{success}</p>
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-300">{error}</p>
              </div>
            )}

            <form onSubmit={handlePasswordChange} className="space-y-6">
              {/* Current Password */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                  placeholder="Enter current password"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                           text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                           focus:ring-4 focus:ring-gold-500/10 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>

              {/* New Password */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                  placeholder="Enter new password (min 6 characters)"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                           text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                           focus:ring-4 focus:ring-gold-500/10 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Confirm Password */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                  placeholder="Confirm new password"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                           text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                           focus:ring-4 focus:ring-gold-500/10 transition-all"
                  required
                  disabled={isLoading}
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="btn-gold w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <>
                    <div className="w-5 h-5 border-2 border-t-transparent border-gold-900 rounded-full animate-spin"></div>
                    <span>Updating...</span>
                  </>
                ) : (
                  <>
                    <Lock className="w-5 h-5" />
                    <span>Update Password</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default SuperAdminSettings
