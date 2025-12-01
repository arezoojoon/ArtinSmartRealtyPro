/**
 * Super Admin Dashboard - Tenant Management & Impersonation
 * Allows Super Admin to view all tenants and access their dashboards
 */

import React, { useState, useEffect } from 'react';
import { Layout } from './Layout';
import { Eye, Users, Calendar, TrendingUp, AlertTriangle } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const SuperAdminDashboard = ({ user, onLogout, onImpersonate }) => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [tenants, setTenants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    total_tenants: 0,
    active_tenants: 0,
    trial_tenants: 0,
    total_leads: 0
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
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Super Admin Dashboard</h1>
          <p className="text-gray-400">Manage tenants and access their dashboards</p>
        </div>

        {error && (
          <div className="glass-card border-2 border-red-500/50 bg-red-500/10 rounded-xl px-6 py-4 text-red-400">
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
            </table>

            {tenants.length === 0 && (
              <div className="text-center py-16">
                <p className="text-gray-500 text-lg">No tenants found.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default SuperAdminDashboard;
