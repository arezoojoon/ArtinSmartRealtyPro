import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Lock, User, AlertCircle } from 'lucide-react'
import goldLogo from '../goldlogo.svg'

const Login = () => {
  const navigate = useNavigate()
  const { login, isLoading, error } = useAuth()
  const [rememberMe, setRememberMe] = useState(false)
  
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    const result = await login(formData.username, formData.password)
    
    if (result.success) {
      navigate('/')
    }
  }

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    })
  }

  return (
    <div className="min-h-screen bg-navy-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-radial from-gold-500/5 via-transparent to-transparent"></div>
      <div className="absolute top-20 left-10 w-72 h-72 bg-gold-500/5 rounded-full blur-3xl"></div>
      <div className="absolute bottom-20 right-10 w-96 h-96 bg-gold-500/3 rounded-full blur-3xl"></div>

      {/* Login Container */}
      <div className="relative z-10 min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Logo & Title */}
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-24 h-24 mb-4">
              <img src={goldLogo} alt="Artin Expo" className="w-24 h-24" />
            </div> 
            <h1 className="text-4xl font-bold gradient-text-gold mb-2">
              Artin Expo Smart Agent 
            </h1>
            <p className="text-white/50">
              Enterprise Exhibitions Management Platform
            </p>
          </div>

          {/* Login Form */}
          <div className="glass-card rounded-2xl p-8 shadow-2xl">
            <h2 className="text-2xl font-bold text-white mb-6">
              Sign In to Your Account
            </h2>

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-start gap-3 animate-fade-in">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-semibold text-red-400">Login Failed</p>
                  <p className="text-sm text-red-300/80">{error}</p>
                </div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Username Field */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  Username
                </label>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    placeholder="Enter your username"
                    className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                             text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                             focus:ring-4 focus:ring-gold-500/10 transition-all"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              {/* Password Field */}
              <div>
                <label className="block text-sm font-medium text-white/70 mb-2">
                  Password
                </label>
                <div className="relative">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-white/40" />
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    placeholder="Enter your password"
                    className="w-full pl-12 pr-4 py-3 bg-white/5 border border-white/10 rounded-xl 
                             text-white placeholder-white/30 focus:outline-none focus:border-gold-500/40 
                             focus:ring-4 focus:ring-gold-500/10 transition-all"
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              {/* Remember Me & Forgot Password */}
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-white/20 bg-white/5 
                             checked:bg-gold-500 checked:border-gold-500 
                             focus:ring-2 focus:ring-gold-500/20"
                  />
                  <span className="text-sm text-white/60">Remember me</span>
                </label>
                <Link to="/forgot-password" className="text-sm text-gold-500 hover:text-gold-400 transition-colors">
                  Forgot password?
                </Link>
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
                    <span>Signing in...</span>
                  </>
                ) : (
                  <span>Sign In</span>
                )}
              </button>
            </form>

            {/* Sign Up Link */}
            <div className="mt-6 text-center">
              <p className="text-sm text-white/60">
                Don't have an account?{' '}
                <a 
                  href="mailto:sales@artinexpo.com?subject=New Account Request&body=I would like to create an account for the Exhibition Booth Platform"
                  className="text-gold-500 hover:text-gold-400 font-semibold transition-colors"
                >
                  Contact Sales
                </a>
              </p>
              <p className="text-xs text-white/40 mt-2">
                📧 Or email: sales@artinexpo.com
              </p>
            </div>

            {/* Footer */}
            <div className="mt-6 pt-6 border-t border-white/10 text-center">
              <p className="text-sm text-white/50">
                Exhibitions Platform v2.1
              </p>
              <p className="text-xs text-white/30 mt-1">
                Powered by Artin Smart Agent 
              </p>
            </div>
          </div>

          {/* Company Info */}
          <div className="mt-6 glass-card rounded-xl p-4 text-center">
            <p className="text-sm text-white/50 mb-2">🏢 AMHR Marketing Management LLC</p>
            <p className="text-xs text-gold-400 font-mono">
               🌍 Serving exhibitions in UAE, Canada & worldwide
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Login
