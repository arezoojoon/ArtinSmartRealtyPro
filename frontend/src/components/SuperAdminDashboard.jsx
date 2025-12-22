/**
 * Super Admin Dashboard - God Mode
 * Platform owner control panel with tenant management, monitoring, and billing
 */

import React, { useState, useEffect } from 'react';
import {
  Users,
  Eye,
  Power,
  AlertTriangle,
  TrendingUp,
  DollarSign,
  Server,
  Cpu,
  HardDrive,
  Key,
  Calendar,
  Plus,
  X,
  Search,
  Filter,
  MoreVertical,
  RefreshCw,
  Download,
  Zap,
  Activity,
  CheckCircle,
  XCircle,
  Clock,
  BarChart3,
  Wallet,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const SuperAdminDashboard = ({ user, onLogout, onImpersonate }) => {
  const [tenants, setTenants] = useState([]);
  const [selectedTenant, setSelectedTenant] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tenants');
  const [showCreateTenant, setShowCreateTenant] = useState(false);
  const [showLicenseModal, setShowLicenseModal] = useState(false);
  const [newTenant, setNewTenant] = useState({ email: '', name: '', company_name: '', password: '' });
  const [searchQuery, setSearchQuery] = useState('');

  // Monitoring State
  const [tokenUsage, setTokenUsage] = useState([]);
  const [systemErrors, setSystemErrors] = useState([]);
  const [serverStatus, setServerStatus] = useState({ cpu: 0, ram: 0, containers: [] });

  // Billing State
  const [mrrData, setMrrData] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [licenseKeys, setLicenseKeys] = useState([]);

  const token = localStorage.getItem('token');

  // Fetch all data
  useEffect(() => {
    fetchTenants();
    fetchMonitoringData();
    fetchBillingData();
  }, []);

  const fetchTenants = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/tenants`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setTenants(Array.isArray(data) ? data : (data.tenants || []));
      }
    } catch (error) {
      console.error('Error fetching tenants:', error);
      // Sample data for demo
      setTenants([
        { id: 1, name: 'Palm Realty Dubai', email: 'admin@palmrealty.ae', subscription_status: 'active', created_at: '2024-01-15', leads_count: 245 },
        { id: 2, name: 'Marina Properties', email: 'info@marinaprop.com', subscription_status: 'active', created_at: '2024-02-20', leads_count: 189 },
        { id: 3, name: 'Downtown Estates', email: 'contact@downtown.ae', subscription_status: 'trial', created_at: '2024-03-10', leads_count: 56 },
        { id: 4, name: 'JBR Investments', email: 'hello@jbrinvest.com', subscription_status: 'suspended', created_at: '2024-01-05', leads_count: 312 },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchMonitoringData = async () => {
    try {
      // Fetch token usage
      const tokenRes = await fetch(`${API_BASE_URL}/api/v1/admin/monitoring/tokens`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (tokenRes.ok) {
        const data = await tokenRes.json();
        setTokenUsage(data);
      }

      // Fetch system errors
      const errorRes = await fetch(`${API_BASE_URL}/api/v1/admin/monitoring/errors`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (errorRes.ok) {
        const data = await errorRes.json();
        setSystemErrors(data);
      }

      // Fetch server status
      const serverRes = await fetch(`${API_BASE_URL}/api/v1/admin/monitoring/servers`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (serverRes.ok) {
        const data = await serverRes.json();
        setServerStatus(data);
      }
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      // Sample data for demo
      setTokenUsage([
        { tenant: 'Palm Realty Dubai', tokens: 45000, cost: 2.25 },
        { tenant: 'Marina Properties', tokens: 32000, cost: 1.60 },
        { tenant: 'Downtown Estates', tokens: 12000, cost: 0.60 },
      ]);
      setSystemErrors([
        { id: 1, type: 'warning', message: 'Telegram API timeout', timestamp: '2024-12-21 10:30', resolved: false },
        { id: 2, type: 'error', message: 'Database connection pool exhausted', timestamp: '2024-12-21 09:15', resolved: true },
        { id: 3, type: 'info', message: 'WhatsApp session reconnected', timestamp: '2024-12-21 08:00', resolved: true },
      ]);
      setServerStatus({
        cpu: 45, ram: 62, containers: [
          { name: 'backend', status: 'running', cpu: 15, ram: 512 },
          { name: 'postgres', status: 'running', cpu: 8, ram: 256 },
          { name: 'redis', status: 'running', cpu: 2, ram: 128 },
          { name: 'nginx', status: 'running', cpu: 1, ram: 64 },
        ]
      });
    }
  };

  const fetchBillingData = async () => {
    try {
      // Fetch MRR
      const mrrRes = await fetch(`${API_BASE_URL}/api/v1/admin/billing/mrr`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (mrrRes.ok) {
        const data = await mrrRes.json();
        setMrrData(data);
      }

      // Fetch invoices
      const invRes = await fetch(`${API_BASE_URL}/api/v1/admin/billing/invoices`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (invRes.ok) {
        const data = await invRes.json();
        setInvoices(data);
      }
    } catch (error) {
      console.error('Error fetching billing data:', error);
      // Sample data for demo
      setMrrData([
        { month: 'Jul', revenue: 8500 },
        { month: 'Aug', revenue: 12000 },
        { month: 'Sep', revenue: 15500 },
        { month: 'Oct', revenue: 18200 },
        { month: 'Nov', revenue: 22000 },
        { month: 'Dec', revenue: 25500 },
      ]);
      setInvoices([
        { id: 'INV-001', tenant: 'Palm Realty Dubai', amount: 499, status: 'paid', date: '2024-12-01' },
        { id: 'INV-002', tenant: 'Marina Properties', amount: 299, status: 'paid', date: '2024-12-01' },
        { id: 'INV-003', tenant: 'Downtown Estates', amount: 0, status: 'trial', date: '2024-12-10' },
        { id: 'INV-004', tenant: 'JBR Investments', amount: 499, status: 'overdue', date: '2024-11-01' },
      ]);
    }
  };

  // Tenant Actions
  const handleImpersonate = (tenant) => {
    sessionStorage.setItem('admin_fallback_token', token);
    sessionStorage.setItem('impersonating_tenant', JSON.stringify(tenant));
    onImpersonate(tenant);
  };

  const handleSuspendTenant = async (tenantId) => {
    if (!confirm('Are you sure you want to suspend this tenant? They will lose access immediately.')) return;

    try {
      await fetch(`${API_BASE_URL}/api/v1/admin/tenants/${tenantId}/suspend`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchTenants();
    } catch (error) {
      console.error('Error suspending tenant:', error);
      // Update UI optimistically
      setTenants(tenants.map(t =>
        t.id === tenantId ? { ...t, subscription_status: 'suspended' } : t
      ));
    }
  };

  const handleActivateTenant = async (tenantId) => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/admin/tenants/${tenantId}/activate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      fetchTenants();
    } catch (error) {
      console.error('Error activating tenant:', error);
      setTenants(tenants.map(t =>
        t.id === tenantId ? { ...t, subscription_status: 'active' } : t
      ));
    }
  };

  const handleChangePlan = async (tenantId, newPlan) => {
    try {
      await fetch(`${API_BASE_URL}/api/v1/admin/tenants/${tenantId}/plan`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ plan: newPlan })
      });
      fetchTenants();
    } catch (error) {
      console.error('Error changing plan:', error);
    }
  };

  const handleGenerateLicense = async (tenantId, plan) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/admin/billing/license`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tenant_id: tenantId, plan })
      });
      if (response.ok) {
        const data = await response.json();
        alert(`License Key Generated: ${data.license_key}`);
        setLicenseKeys([...licenseKeys, data]);
      }
    } catch (error) {
      console.error('Error generating license:', error);
      // Generate sample key for demo
      const key = `LIC-${Date.now().toString(36).toUpperCase()}-${Math.random().toString(36).substr(2, 8).toUpperCase()}`;
      alert(`License Key Generated: ${key}`);
    }
  };

  const handleCreateTenant = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/tenants`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newTenant)
      });
      if (response.ok) {
        setShowCreateTenant(false);
        setNewTenant({ email: '', name: '', company_name: '', password: '' });
        fetchTenants();
        alert('Tenant created successfully!');
      } else {
        const error = await response.json();
        alert(`Error: ${error.detail || 'Failed to create tenant'}`);
      }
    } catch (error) {
      console.error('Error creating tenant:', error);
      alert('Failed to create tenant. Please try again.');
    }
  };

  // Status Badge Component
  const StatusBadge = ({ status }) => {
    const config = {
      active: { class: 'badge-green', icon: CheckCircle, label: 'Active' },
      trial: { class: 'badge-blue', icon: Clock, label: 'Trial' },
      suspended: { class: 'badge-red', icon: XCircle, label: 'Suspended' },
      overdue: { class: 'badge-yellow', icon: AlertTriangle, label: 'Overdue' },
      paid: { class: 'badge-green', icon: CheckCircle, label: 'Paid' },
    };
    const { class: badgeClass, icon: Icon, label } = config[status] || config.active;

    return (
      <span className={`badge ${badgeClass} flex items-center gap-1`}>
        <Icon className="w-3 h-3" />
        {label}
      </span>
    );
  };

  // Filter tenants by search
  const filteredTenants = tenants.filter(t =>
    t.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.email?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Calculate total MRR
  const totalMRR = mrrData.length > 0 ? mrrData[mrrData.length - 1].revenue : 0;
  const maxMRR = Math.max(...mrrData.map(d => d.revenue), 1);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 flex items-center justify-center">
        <div className="spinner" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800">
      {/* Header */}
      <header className="glass-header px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center">
            <Zap className="w-6 h-6 text-navy-900" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Super Admin</h1>
            <p className="text-xs text-gold-400">God Mode Active</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <button onClick={fetchTenants} className="btn-icon" title="Refresh">
            <RefreshCw className="w-5 h-5" />
          </button>
          <button onClick={onLogout} className="btn-outline">
            Logout
          </button>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="px-6 pt-6">
        <div className="flex gap-2 p-1 bg-navy-800/50 rounded-xl inline-flex">
          {[
            { id: 'tenants', label: 'Tenant Management', icon: Users },
            { id: 'monitoring', label: 'AI & Monitoring', icon: Activity },
            { id: 'billing', label: 'Billing & Finance', icon: DollarSign },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${activeTab === tab.id
                ? 'bg-gold-500/20 text-gold-400'
                : 'text-gray-400 hover:text-white'
                }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {/* TENANT MANAGEMENT TAB */}
        {activeTab === 'tenants' && (
          <div className="space-y-6">
            {/* Stats Row */}
            <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon"><Users className="w-6 h-6 text-gold-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">{tenants.length}</p>
                    <p className="text-sm text-gray-400">Total Tenants</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon bg-green-500/20"><CheckCircle className="w-6 h-6 text-green-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">{tenants.filter(t => t.subscription_status === 'active').length}</p>
                    <p className="text-sm text-gray-400">Active</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon bg-blue-500/20"><Clock className="w-6 h-6 text-blue-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">{tenants.filter(t => t.subscription_status === 'trial').length}</p>
                    <p className="text-sm text-gray-400">On Trial</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon bg-red-500/20"><XCircle className="w-6 h-6 text-red-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">{tenants.filter(t => t.subscription_status === 'suspended').length}</p>
                    <p className="text-sm text-gray-400">Suspended</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Search and Actions */}
            <div className="flex items-center justify-between gap-4">
              <div className="relative flex-1 max-w-md">
                <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search tenants..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input w-full pl-12"
                />
              </div>
              <button
                onClick={() => setShowCreateTenant(true)}
                className="btn-gold flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Add Tenant
              </button>
            </div>

            {/* Tenant Table */}
            <div className="glass-card overflow-hidden">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Tenant</th>
                    <th>Email</th>
                    <th>Status</th>
                    <th>Leads</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTenants.map((tenant) => (
                    <tr key={tenant.id}>
                      <td className="font-medium text-white">{tenant.name}</td>
                      <td>{tenant.email}</td>
                      <td><StatusBadge status={tenant.subscription_status} /></td>
                      <td>{tenant.leads_count || 0}</td>
                      <td>{new Date(tenant.created_at).toLocaleDateString()}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleImpersonate(tenant)}
                            className="p-2 rounded-lg hover:bg-navy-700 text-blue-400 transition-all"
                            title="Impersonate"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {tenant.subscription_status === 'suspended' ? (
                            <button
                              onClick={() => handleActivateTenant(tenant.id)}
                              className="p-2 rounded-lg hover:bg-green-500/20 text-green-400 transition-all"
                              title="Activate"
                            >
                              <Power className="w-4 h-4" />
                            </button>
                          ) : (
                            <button
                              onClick={() => handleSuspendTenant(tenant.id)}
                              className="p-2 rounded-lg hover:bg-red-500/20 text-red-400 transition-all"
                              title="Kill Switch"
                            >
                              <Power className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => handleGenerateLicense(tenant.id, 'lifetime')}
                            className="p-2 rounded-lg hover:bg-gold-500/20 text-gold-400 transition-all"
                            title="Generate License"
                          >
                            <Key className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MONITORING TAB */}
        {activeTab === 'monitoring' && (
          <div className="space-y-6">
            {/* Token Usage */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-gold-400" />
                AI Token Usage (This Month)
              </h3>
              <div className="space-y-4">
                {tokenUsage.map((item, index) => (
                  <div key={index} className="flex items-center gap-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-white">{item.tenant}</span>
                        <span className="text-sm text-gray-400">{item.tokens.toLocaleString()} tokens</span>
                      </div>
                      <div className="h-2 bg-navy-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-gold-400 to-gold-600 rounded-full"
                          style={{ width: `${Math.min((item.tokens / 50000) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                    <span className="text-sm text-gold-400 font-medium w-16 text-right">${item.cost}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Server Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <Server className="w-5 h-5 text-gold-400" />
                  Server Status
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-navy-800/50 rounded-xl p-4 text-center">
                    <Cpu className="w-8 h-8 text-blue-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">{serverStatus.cpu}%</p>
                    <p className="text-xs text-gray-400">CPU Usage</p>
                  </div>
                  <div className="bg-navy-800/50 rounded-xl p-4 text-center">
                    <HardDrive className="w-8 h-8 text-purple-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">{serverStatus.ram}%</p>
                    <p className="text-xs text-gray-400">RAM Usage</p>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  {serverStatus.containers?.map((container, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-navy-800/30 rounded-lg">
                      <div className="flex items-center gap-2">
                        <span className={`w-2 h-2 rounded-full ${container.status === 'running' ? 'bg-green-400' : 'bg-red-400'}`} />
                        <span className="text-sm text-white">{container.name}</span>
                      </div>
                      <span className="text-xs text-gray-400">{container.ram}MB</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Error Monitoring */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-yellow-400" />
                  System Errors
                </h3>
                <div className="space-y-3 max-h-[300px] overflow-y-auto">
                  {systemErrors.map((error) => (
                    <div
                      key={error.id}
                      className={`p-3 rounded-lg border-l-4 ${error.type === 'error' ? 'border-l-red-500 bg-red-500/5' :
                        error.type === 'warning' ? 'border-l-yellow-500 bg-yellow-500/5' :
                          'border-l-blue-500 bg-blue-500/5'
                        }`}
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <p className="text-sm text-white">{error.message}</p>
                          <p className="text-xs text-gray-500 mt-1">{error.timestamp}</p>
                        </div>
                        <span className={`badge ${error.resolved ? 'badge-green' : 'badge-yellow'}`}>
                          {error.resolved ? 'Resolved' : 'Active'}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* BILLING TAB */}
        {activeTab === 'billing' && (
          <div className="space-y-6">
            {/* MRR Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon"><DollarSign className="w-6 h-6 text-gold-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">${totalMRR.toLocaleString()}</p>
                    <p className="text-sm text-gray-400">Monthly Revenue (MRR)</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon bg-green-500/20"><TrendingUp className="w-6 h-6 text-green-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">+16%</p>
                    <p className="text-sm text-gray-400">Growth Rate</p>
                  </div>
                </div>
              </div>
              <div className="glass-card p-5">
                <div className="flex items-center gap-4">
                  <div className="kpi-icon"><Wallet className="w-6 h-6 text-gold-400" /></div>
                  <div>
                    <p className="text-2xl font-bold text-white">${(totalMRR * 12).toLocaleString()}</p>
                    <p className="text-sm text-gray-400">ARR (Annual)</p>
                  </div>
                </div>
              </div>
            </div>

            {/* MRR Chart */}
            <div className="glass-card p-6">
              <h3 className="text-lg font-semibold text-white mb-6 flex items-center gap-2">
                <BarChart3 className="w-5 h-5 text-gold-400" />
                Revenue Trend
              </h3>
              <div className="flex items-end gap-4 h-48">
                {mrrData.map((item, index) => (
                  <div key={index} className="flex-1 flex flex-col items-center gap-2">
                    <div
                      className="w-full bg-gradient-to-t from-gold-500 to-gold-400 rounded-t-lg transition-all hover:from-gold-400 hover:to-gold-300"
                      style={{ height: `${(item.revenue / maxMRR) * 100}%` }}
                    />
                    <span className="text-xs text-gray-400">{item.month}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Invoices Table */}
            <div className="glass-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  Invoices
                </h3>
                <button className="btn-outline flex items-center gap-2 text-sm">
                  <Download className="w-4 h-4" />
                  Export
                </button>
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Invoice ID</th>
                    <th>Tenant</th>
                    <th>Amount</th>
                    <th>Status</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {invoices.map((invoice) => (
                    <tr key={invoice.id}>
                      <td className="font-mono text-gold-400">{invoice.id}</td>
                      <td>{invoice.tenant}</td>
                      <td className="font-medium text-white">${invoice.amount}</td>
                      <td><StatusBadge status={invoice.status} /></td>
                      <td>{new Date(invoice.date).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Create Tenant Modal */}
      {showCreateTenant && (
        <div className="modal-overlay" onClick={() => setShowCreateTenant(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-white">Add New Tenant</h3>
              <button onClick={() => setShowCreateTenant(false)} className="text-gray-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateTenant} className="space-y-4">
              <div>
                <label className="input-label">Name</label>
                <input
                  type="text"
                  value={newTenant.name}
                  onChange={(e) => setNewTenant({ ...newTenant, name: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="input-label">Email</label>
                <input
                  type="email"
                  value={newTenant.email}
                  onChange={(e) => setNewTenant({ ...newTenant, email: e.target.value })}
                  className="input-field"
                  required
                />
              </div>
              <div>
                <label className="input-label">Company Name</label>
                <input
                  type="text"
                  value={newTenant.company_name}
                  onChange={(e) => setNewTenant({ ...newTenant, company_name: e.target.value })}
                  className="input-field"
                />
              </div>
              <div>
                <label className="input-label">Password</label>
                <input
                  type="password"
                  value={newTenant.password}
                  onChange={(e) => setNewTenant({ ...newTenant, password: e.target.value })}
                  className="input-field"
                  required
                  minLength={8}
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button type="button" onClick={() => setShowCreateTenant(false)} className="flex-1 btn-ghost">
                  Cancel
                </button>
                <button type="submit" className="flex-1 btn-gold">
                  Create Tenant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SuperAdminDashboard;
