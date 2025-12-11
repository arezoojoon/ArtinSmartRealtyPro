import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../context/AuthContext'
import { Building2, Lock, CheckCircle, AlertCircle } from 'lucide-react'

const ResetPassword = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  useEffect(() => {
    if (!token) {
      setError('Invalid or missing reset token')
    }
  }, [token])

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      await api.post('/api/auth/reset-password', {
        token,
        new_password: formData.password
      })
      setSuccess(true)
      setTimeout(() => navigate('/login'), 3000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to reset password. Token may have expired.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-navy-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-radial from-gold-500/5 via-transparent to-transparent"></div>
      <div className="absolute top-20 left-10 w-72 h-72 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>

      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Logo & Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-gold rounded-2xl mb-4 shadow-gold">
              <Building2 className="w-8 h-8 text-navy-900" />
            </div>
            <h1 className="text-3xl font-bold gradient-text-gold mb-2">
              Set New Password
            </h1>
            <p className="text-white/50">
              Choose a strong password for your account
            </p>
          </div>

          {/* Form Container */}
          <div className="glass-card rounded-2xl p-8 shadow-2xl">
            {success ? (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500/10 rounded-full mb-4">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Password Reset!</h2>
                <p className="text-white/60 mb-4">
                  Your password has been successfully reset.
                </p>
                <p className="text-sm text-gold-400">
                  Redirecting to login...
                </p>
              </div>
            ) : (
              <>
                <h2 className="text-2xl font-bold text-white mb-6">
                  Reset Password
                </h2>

                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* New Password */}
                  <div>
                    <label className="block text-sm font-medium text-white/70 mb-2">
                      New Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                      <input
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({...formData, password: e.target.value})}
                        placeholder="Enter new password"
                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                                 text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                                 focus:ring-4 focus:ring-gold-500/10 transition-all"
                        required
                        disabled={isLoading || !token}
                        minLength={6}
                      />
                    </div>
                  </div>

                  {/* Confirm Password */}
                  <div>
                    <label className="block text-sm font-medium text-white/70 mb-2">
                      Confirm Password
                    </label>
                    <div className="relative">
                      <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                      <input
                        type="password"
                        value={formData.confirmPassword}
                        onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                        placeholder="Confirm new password"
                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                                 text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                                 focus:ring-4 focus:ring-gold-500/10 transition-all"
                        required
                        disabled={isLoading || !token}
                        minLength={6}
                      />
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={isLoading || !token}
                    className="btn-gold w-full flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-5 h-5 border-2 border-t-transparent border-gold-900 rounded-full animate-spin"></div>
                        <span>Resetting...</span>
                      </>
                    ) : (
                      <span>Reset Password</span>
                    )}
                  </button>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ResetPassword
