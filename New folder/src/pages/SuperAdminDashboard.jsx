/**
 * Super Admin Dashboard - Tenant Management & Impersonation
 * Allows Super Admin to view all tenants and impersonate them
 */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, LogOut, Users, Building2, TrendingUp, Calendar } from 'lucide-react'
import { Layout } from '../components/Layout'
import { api } from '../context/AuthContext'

const SuperAdminDashboard = () => {
  const navigate = useNavigate()
  const [tenants, setTenants] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchTenants()
  }, [])

  const fetchTenants = async () => {
    try {
      setLoading(true)
      const response = await api.get('/api/admin/tenants')
      setTenants(response.data)
      setError(null)
    } catch (err) {
      console.error('Failed to fetch tenants:', err)
      setError('Failed to load tenants. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleImpersonate = async (tenant) => {
    try {
      // Store current super admin token for fallback
      const currentToken = localStorage.getItem('auth-storage')
      sessionStorage.setItem('admin_fallback_token', currentToken)
      
      // Mark as impersonating
      sessionStorage.setItem('impersonating', JSON.stringify({
        tenantId: tenant.id,
        tenantName: tenant.company_name,
        timestamp: new Date().toISOString()
      }))

      // Get impersonation token
      const response = await api.post(`/api/admin/impersonate/${tenant.id}`)
      const { access_token, user } = response.data

      // Update auth store with impersonated user
      const authStorage = JSON.parse(localStorage.getItem('auth-storage') || '{}')
      authStorage.state = {
        ...authStorage.state,
        user,
        token: access_token,
        isAuthenticated: true
      }
      localStorage.setItem('auth-storage', JSON.stringify(authStorage))

      // Force reload to update auth context
      window.location.href = '/'
    } catch (err) {
      console.error('Impersonation failed:', err)
      const errorMsg = err.response?.data?.detail || err.message || 'Unknown error'
      alert(`Failed to access tenant dashboard: ${errorMsg}`)
      
      // Clean up if failed
      sessionStorage.removeItem('admin_fallback_token')
      sessionStorage.removeItem('impersonating')
    }
  }

  const filteredTenants = tenants.filter(tenant =>
    tenant.company_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    tenant.subdomain?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const getStatusBadge = (status) => {
    const badges = {
      active: 'bg-green-500/20 text-green-300 border-green-500/30',
      trial: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
      expired: 'bg-red-500/20 text-red-300 border-red-500/30',
      inactive: 'bg-gray-500/20 text-gray-300 border-gray-500/30'
    }
    return badges[status] || badges.inactive
  }

  return (
    <Layout>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 p-6">
        {/* Header */}
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                🛡️ Super Admin Dashboard
              </h1>
              <p className="text-blue-200">
                Manage all tenants and access their dashboards
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-blue-300 mb-1">Total Tenants</div>
              <div className="text-3xl font-bold text-white">{tenants.length}</div>
            </div>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            {[
              { icon: Building2, label: 'Active Tenants', value: tenants.filter(t => t.is_active).length, color: 'green' },
              { icon: Users, label: 'Trial Accounts', value: tenants.filter(t => t.subscription_status === 'trial').length, color: 'amber' },
              { icon: TrendingUp, label: 'Total Leads', value: tenants.reduce((sum, t) => sum + (t.total_leads || 0), 0), color: 'blue' },
              { icon: Calendar, label: 'This Month', value: tenants.filter(t => new Date(t.created_at) > new Date(Date.now() - 30*24*60*60*1000)).length, color: 'purple' }
            ].map((stat, idx) => (
              <div key={idx} className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-blue-200">{stat.label}</p>
                    <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  </div>
                  <stat.icon className={`w-10 h-10 text-${stat.color}-400 opacity-60`} />
                </div>
              </div>
            ))}
          </div>

          {/* Search Bar */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 p-4 mb-6">
            <input
              type="text"
              placeholder="🔍 Search by company name or subdomain..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-white/5 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-blue-300/50 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* Tenants Table */}
        <div className="max-w-7xl mx-auto">
          <div className="bg-white/10 backdrop-blur-md rounded-xl border border-white/20 overflow-hidden">
            {loading ? (
              <div className="p-12 text-center">
                <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
                <p className="text-blue-200 mt-4">Loading tenants...</p>
              </div>
            ) : error ? (
              <div className="p-12 text-center">
                <p className="text-red-400">{error}</p>
                <button
                  onClick={fetchTenants}
                  className="mt-4 px-6 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/20">
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">ID</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">Agency Name</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">Subdomain</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">Status</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">Total Leads</th>
                      <th className="px-6 py-4 text-left text-sm font-semibold text-blue-200">Created</th>
                      <th className="px-6 py-4 text-right text-sm font-semibold text-blue-200">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTenants.length === 0 ? (
                      <tr>
                        <td colSpan="7" className="px-6 py-12 text-center text-blue-300">
                          {searchTerm ? 'No tenants found matching your search.' : 'No tenants available.'}
                        </td>
                      </tr>
                    ) : (
                      filteredTenants.map((tenant) => (
                        <tr
                          key={tenant.id}
                          className="border-b border-white/10 hover:bg-white/5 transition-colors"
                        >
                          <td className="px-6 py-4 text-white font-mono text-sm">#{tenant.id}</td>
                          <td className="px-6 py-4">
                            <div className="flex items-center">
                              <Building2 className="w-5 h-5 text-amber-400 mr-2" />
                              <span className="text-white font-medium">{tenant.company_name}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-blue-200 font-mono text-sm">
                            {tenant.subdomain}
                          </td>
                          <td className="px-6 py-4">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getStatusBadge(tenant.is_active ? 'active' : 'inactive')}`}>
                              {tenant.is_active ? '✅ Active' : '⛔ Inactive'}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center text-white">
                              <Users className="w-4 h-4 text-blue-400 mr-2" />
                              <span className="font-semibold">{tenant.total_leads || 0}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-blue-200 text-sm">
                            {new Date(tenant.created_at).toLocaleDateString('en-US', {
                              year: 'numeric',
                              month: 'short',
                              day: 'numeric'
                            })}
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => handleImpersonate(tenant)}
                              className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white rounded-lg transition-all duration-200 shadow-lg hover:shadow-amber-500/50 transform hover:scale-105"
                            >
                              <Eye className="w-4 h-4" />
                              Access Dashboard
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Info Footer */}
        <div className="max-w-7xl mx-auto mt-6">
          <div className="bg-amber-500/10 backdrop-blur-md rounded-xl border border-amber-500/30 p-4">
            <div className="flex items-start gap-3">
              <div className="text-amber-400 text-xl">⚠️</div>
              <div>
                <h3 className="text-amber-300 font-semibold mb-1">Impersonation Mode</h3>
                <p className="text-amber-200/80 text-sm">
                  When you access a tenant's dashboard, you'll see their data as if you were logged in as them. 
                  A warning banner will appear at the top. Click "Exit to Super Admin" to return.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  )
}

export default SuperAdminDashboard
