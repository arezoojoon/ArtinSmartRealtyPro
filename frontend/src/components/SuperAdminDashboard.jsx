/**
 * Super Admin Dashboard - Tenant Management & Impersonation
 * Allows Super Admin to view all tenants and access their dashboards
 */

import React, { useState, useEffect } from 'react';
import { Layout } from './Layout';
import { Eye, Users, Calendar, TrendingUp, AlertTriangle, Plus, X } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const SuperAdminDashboard = ({ user, onLogout, onImpersonate }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [stats, setStats] = useState({
    total_tenants: 0,
    active_tenants: 0,
    trial_tenants: 0,
    total_leads: 0
  });
  const [newTenant, setNewTenant] = useState({
    name: '',
    email: '',
    password: '',
    company_name: '',
    subscription_status: 'trial'
  });

  useEffect(() => {
    fetchTenants();
  }, []);

  const fetchTenants = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${API_BASE_URL}/api/tenants`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Failed to fetch tenants');
      
      const data = await response.json();
      setTenants(data);
      
      // Calculate stats
      setStats({
        total_tenants: data.length,
        active_tenants: data.filter(t => t.subscription_status === 'active').length,
        trial_tenants: data.filter(t => t.subscription_status === 'trial').length,
        total_leads: data.reduce((sum, t) => sum + (t.total_leads || 0), 0)
      });
      
      setError(null);
    } catch (err) {
      console.error('Failed to fetch tenants:', err);
      setError('Failed to load tenant data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleImpersonate = async (tenant) => {
    try {
      // Store current admin token for restoration
      const adminToken = localStorage.getItem('token');
      sessionStorage.setItem('admin_fallback_token', adminToken);
      sessionStorage.setItem('impersonating_tenant', JSON.stringify({
        id: tenant.id,
        name: tenant.name,
        email: tenant.email
      }));

      // Call impersonation function passed from parent
      if (onImpersonate) {
        await onImpersonate(tenant);
      }
    } catch (err) {
      console.error('Impersonation failed:', err);
      alert('Failed to access tenant dashboard. Please try again.');
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: 'badge-green',
      trial: 'badge-yellow',
      suspended: 'badge-red',
      expired: 'badge-red'
    };
    return badges[status] || 'badge-blue';
  };

  const getStatusText = (status) => {
    return status ? status.charAt(0).toUpperCase() + status.slice(1) : 'Unknown';
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    
    try {
      setCreating(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          name: newTenant.name,
          email: newTenant.email,
          password: newTenant.password,
          company_name: newTenant.company_name
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create tenant');
      }

      // Reset form and close modal
      setNewTenant({
        name: '',
        email: '',
        password: '',
        company_name: '',
        subscription_status: 'trial'
      });
      setShowCreateModal(false);
      
      // Refresh tenant list
      await fetchTenants();
      
      alert('✅ Tenant created successfully!');
    } catch (err) {
      console.error('Failed to create tenant:', err);
      alert(`❌ Failed to create tenant: ${err.message}`);
    } finally {
      setCreating(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-navy-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-400 text-lg">Loading tenant data...</p>
        </div>
      </div>
    );
  }

  return (
    <Layout activeTab={activeTab} setActiveTab={setActiveTab} user={user} onLogout={onLogout}>
      <div className="space-y-8 animate-fade-in">
        {/* Tenants Table */}
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/10 flex items-center justify-between">
            <h3 className="text-white font-bold text-lg flex items-center gap-2">
              <Users size={20} className="text-gold-500" />
              Tenant Management
            </h3>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-gold flex items-center gap-2 text-sm"
            >
              <Plus size={16} />
              Create New Tenant
            </button>
          </div>lassName="glass-card border-2 border-red-500/50 bg-red-500/10 rounded-xl px-6 py-4 text-red-400">
            <AlertTriangle className="inline mr-2" size={20} />
            {error}
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-gold-500 rounded-bl-2xl">
              <Users size={48} />
            </div>
            <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Total Tenants</p>
            <h3 className="text-3xl font-bold text-white mt-2">{stats.total_tenants}</h3>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-green-500 rounded-bl-2xl">
              <TrendingUp size={48} />
            </div>
            <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Active Subscriptions</p>
            <h3 className="text-3xl font-bold text-white mt-2">{stats.active_tenants}</h3>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-yellow-500 rounded-bl-2xl">
              <Calendar size={48} />
            </div>
            <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Trial Accounts</p>
            <h3 className="text-3xl font-bold text-white mt-2">{stats.trial_tenants}</h3>
          </div>

          <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-blue-500 rounded-bl-2xl">
              <Users size={48} />
            </div>
            <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">Total Leads (All)</p>
            <h3 className="text-3xl font-bold text-white mt-2">{stats.total_leads}</h3>
          </div>
        </div>

        {/* Tenants Table */}
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h3 className="text-white font-bold text-lg flex items-center gap-2">
              <Users size={20} className="text-gold-500" />
              Tenant Management
            </h3>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-navy-900/50">
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">ID</th>
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Agency Name</th>
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Admin Email</th>
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Subscription</th>
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Total Leads</th>
                  <th className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Created</th>
                  <th className="text-gold-500 text-center px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">Action</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map(tenant => (
                  <tr key={tenant.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="text-white px-6 py-4 text-sm font-medium">{tenant.id}</td>
                    <td className="text-white px-6 py-4 text-sm font-semibold">{tenant.name || tenant.company_name || 'N/A'}</td>
                    <td className="text-gray-400 px-6 py-4 text-sm">{tenant.email}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold ${getStatusBadge(tenant.subscription_status)}`}>
                        {getStatusText(tenant.subscription_status)}
                      </span>
                    </td>
                    <td className="text-gold-500 px-6 py-4 text-sm font-semibold">{tenant.total_leads || 0}</td>
                    <td className="text-gray-400 px-6 py-4 text-sm">
                      {tenant.created_at ? new Date(tenant.created_at).toLocaleDateString() : 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={() => handleImpersonate(tenant)}
                        className="btn-gold flex items-center gap-2 mx-auto text-sm py-2 px-4"
                        title="Access this tenant's dashboard"
                      >
                        <Eye size={16} />
                        Access Dashboard
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
          </div>
        </div>

        {/* Create Tenant Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="glass-card rounded-2xl w-full max-w-md p-8 relative animate-slide-in-up">
              <button
                onClick={() => setShowCreateModal(false)}
                className="absolute top-4 right-4 text-gray-400 hover:text-white transition-colors"
              >
                <X size={24} />
              </button>

              <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                <Plus size={24} className="text-gold-500" />
                Create New Tenant
              </h2>

              <form onSubmit={handleCreateTenant} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Agency Name *
                  </label>
                  <input
                    type="text"
                    value={newTenant.name}
                    onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                    className="w-full px-4 py-3 bg-navy-900/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500 transition-colors"
                    placeholder="Luxury Properties Dubai"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Company Name *
                  </label>
                  <input
                    type="text"
                    value={newTenant.company_name}
                    onChange={(e) => setNewTenant({ ...newTenant, company_name: e.target.value })}
                    className="w-full px-4 py-3 bg-navy-900/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500 transition-colors"
                    placeholder="Luxury Properties LLC"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Admin Email *
                  </label>
                  <input
                    type="email"
                    value={newTenant.email}
                    onChange={(e) => setNewTenant({ ...newTenant, email: e.target.value })}
                    className="w-full px-4 py-3 bg-navy-900/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500 transition-colors"
                    placeholder="admin@agency.com"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Password *
                  </label>
                  <input
                    type="password"
                    value={newTenant.password}
                    onChange={(e) => setNewTenant({ ...newTenant, password: e.target.value })}
                    className="w-full px-4 py-3 bg-navy-900/50 border border-white/10 rounded-xl text-white focus:outline-none focus:border-gold-500 transition-colors"
                    placeholder="Min 6 characters"
                    minLength={6}
                    required
                  />
                </div>

                <div className="flex gap-3 mt-6">
                  <button
                    type="button"
                    onClick={() => setShowCreateModal(false)}
                    className="flex-1 px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-xl transition-colors"
                    disabled={creating}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="flex-1 btn-gold py-3"
                    disabled={creating}
                  >
                    {creating ? 'Creating...' : 'Create Tenant'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
};

export default SuperAdminDashboard;
        </div>
      </div>
    </Layout>
  );
};

export default SuperAdminDashboard;
