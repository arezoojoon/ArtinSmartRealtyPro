import { useState, useEffect } from 'react';
import { getAllTenants, suspendTenant, activateTenant, impersonateTenant, getMRR, getTokenUsage } from '../../api/client';
import { Building, Power, Eye, TrendingUp, DollarSign, Zap, Server } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

/**
 * Super Admin Dashboard - God Mode
 * Full control over platform, tenants, billing, and resources
 */

const TenantCard = ({ tenant, onSuspend, onActivate, onImpersonate }) => {
  const getStatusColor = () => {
    switch (tenant.status) {
      case 'active': return 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300';
      case 'suspended': return 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300';
      case 'trial': return 'bg-yellow-100 dark:bg-yellow-900 text-yellow-700 dark:text-yellow-300';
      default: return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300';
    }
  };
  
  const getPlanColor = () => {
    switch (tenant.plan) {
      case 'gold': return 'text-yellow-600';
      case 'silver': return 'text-gray-500';
      case 'bronze': return 'text-orange-600';
      default: return 'text-blue-600';
    }
  };
  
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
            {tenant.name.charAt(0)}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{tenant.name}</h3>
            <p className="text-sm text-gray-600 dark:text-gray-400">{tenant.domain || 'No domain'}</p>
          </div>
        </div>
        
        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
          {tenant.status}
        </span>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-600 dark:text-gray-400">Leads</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">{tenant.leads_count || 0}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 dark:text-gray-400">Agents</p>
          <p className="text-xl font-bold text-gray-900 dark:text-white">{tenant.agents_count || 0}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600 dark:text-gray-400">Plan</p>
          <p className={`text-xl font-bold uppercase ${getPlanColor()}`}>{tenant.plan}</p>
        </div>
      </div>
      
      {/* Token Usage */}
      <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-gray-600 dark:text-gray-400">AI Tokens (30d)</span>
          <span className="text-xs font-semibold text-gray-900 dark:text-white">
            {(tenant.token_usage || 0).toLocaleString()}
          </span>
        </div>
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full"
            style={{ width: `${Math.min(100, (tenant.token_usage / 1000000) * 100)}%` }}
          />
        </div>
      </div>
      
      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={() => onImpersonate(tenant.id)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-sm"
        >
          <Eye className="w-4 h-4" />
          Impersonate
        </button>
        
        {tenant.status === 'active' ? (
          <button
            onClick={() => onSuspend(tenant.id)}
            className="px-3 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors"
            title="Kill Switch - Suspend Tenant"
          >
            <Power className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={() => onActivate(tenant.id)}
            className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
            title="Activate Tenant"
          >
            <Power className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
};

export default function SuperAdminDashboard() {
  const [tenants, setTenants] = useState([]);
  const [mrrData, setMrrData] = useState([]);
  const [stats, setStats] = useState({
    totalRevenue: 0,
    activeTenantsCount: 0,
    totalTokensUsed: 0
  });
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadDashboardData();
  }, []);
  
  const loadDashboardData = async () => {
    try {
      const [tenantsRes, mrrRes] = await Promise.all([
        getAllTenants(),
        getMRR()
      ]);
      
      setTenants(tenantsRes.data);
      setMrrData(mrrRes.data.monthly_data || []);
      setStats({
        totalRevenue: mrrRes.data.total_mrr || 0,
        activeTenantsCount: tenantsRes.data.filter(t => t.status === 'active').length,
        totalTokensUsed: tenantsRes.data.reduce((sum, t) => sum + (t.token_usage || 0), 0)
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSuspend = async (tenantId) => {
    if (!confirm('⚠️ Kill Switch: Are you sure you want to suspend this tenant?')) return;
    
    try {
      await suspendTenant(tenantId);
      await loadDashboardData();
      
      // Show notification
      alert('✅ Tenant suspended successfully');
    } catch (error) {
      console.error('Failed to suspend tenant:', error);
      alert('❌ Failed to suspend tenant');
    }
  };
  
  const handleActivate = async (tenantId) => {
    try {
      await activateTenant(tenantId);
      await loadDashboardData();
      alert('✅ Tenant activated successfully');
    } catch (error) {
      console.error('Failed to activate tenant:', error);
      alert('❌ Failed to activate tenant');
    }
  };
  
  const handleImpersonate = async (tenantId) => {
    try {
      const response = await impersonateTenant(tenantId);
      
      // Update auth store and redirect
      const authStore = useAuthStore.getState();
      authStore.impersonate(tenantId, response.data.tenant_name);
      
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Failed to impersonate tenant:', error);
      alert('❌ Failed to impersonate tenant');
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">👑 God Mode</h1>
          <p className="text-gray-600 dark:text-gray-400">Platform-wide control center</p>
        </div>
      </div>
      
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <DollarSign className="w-8 h-8 opacity-80" />
            <TrendingUp className="w-6 h-6" />
          </div>
          <p className="text-sm opacity-90 mb-1">Monthly Recurring Revenue</p>
          <p className="text-4xl font-bold">${stats.totalRevenue.toLocaleString()}</p>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Building className="w-8 h-8 opacity-80" />
            <span className="text-sm opacity-90">Active</span>
          </div>
          <p className="text-sm opacity-90 mb-1">Tenants</p>
          <p className="text-4xl font-bold">{stats.activeTenantsCount}</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-white shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <Zap className="w-8 h-8 opacity-80" />
            <span className="text-xs opacity-90">30 days</span>
          </div>
          <p className="text-sm opacity-90 mb-1">AI Tokens Used</p>
          <p className="text-4xl font-bold">{(stats.totalTokensUsed / 1000000).toFixed(1)}M</p>
        </div>
      </div>
      
      {/* MRR Chart */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Revenue Trend</h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={mrrData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="month" stroke="#9CA3AF" />
            <YAxis stroke="#9CA3AF" />
            <Tooltip
              contentStyle={{
                backgroundColor: '#1F2937',
                border: 'none',
                borderRadius: '8px',
                color: '#fff'
              }}
            />
            <Line
              type="monotone"
              dataKey="revenue"
              stroke="#10B981"
              strokeWidth={3}
              dot={{ fill: '#10B981', r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Tenants Grid */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Tenants Management</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tenants.map(tenant => (
            <TenantCard
              key={tenant.id}
              tenant={tenant}
              onSuspend={handleSuspend}
              onActivate={handleActivate}
              onImpersonate={handleImpersonate}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
