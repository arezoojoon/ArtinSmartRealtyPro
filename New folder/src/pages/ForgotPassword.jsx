import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../context/AuthContext'
import { Building2, Mail, ArrowLeft, CheckCircle, AlertCircle } from 'lucide-react'

const ForgotPassword = () => {
  const [email, setEmail] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setIsLoading(true)
    setError(null)

    try {
      await api.post('/api/auth/forgot-password', { email })
      setSuccess(true)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to send reset email. Please try again.')
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
              Reset Password
            </h1>
            <p className="text-white/50">
              Enter your email to receive reset instructions
            </p>
          </div>

          {/* Form Container */}
          <div className="glass-card rounded-2xl p-8 shadow-2xl">
            {success ? (
              <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-green-500/10 rounded-full mb-4">
                  <CheckCircle className="w-8 h-8 text-green-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">Check Your Email</h2>
                <p className="text-white/60 mb-6">
                  We've sent password reset instructions to <span className="text-gold-400">{email}</span>
                </p>
                <Link 
                  to="/login" 
                  className="btn-gold w-full flex items-center justify-center gap-2"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to Login
                </Link>
              </div>
            ) : (
              <>
                <h2 className="text-2xl font-bold text-white mb-6">
                  Forgot Password?
                </h2>

                {/* Error Message */}
                {error && (
                  <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3">
                    <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-300">{error}</p>
                  </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-6">
                  {/* Email Field */}
                  <div>
                    <label className="block text-sm font-medium text-white/70 mb-2">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                      <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Enter your email"
                        className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                                 text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                                 focus:ring-4 focus:ring-gold-500/10 transition-all"
                        required
                        disabled={isLoading}
                      />
                    </div>
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
                        <span>Sending...</span>
                      </>
                    ) : (
                      <span>Send Reset Link</span>
                    )}
                  </button>

                  {/* Back to Login */}
                  <Link
                    to="/login"
                    className="block text-center text-sm text-white/60 hover:text-gold-400 transition-colors"
                  >
                    <ArrowLeft className="w-4 h-4 inline mr-2" />
                    Back to Login
                  </Link>
                </form>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default ForgotPassword
