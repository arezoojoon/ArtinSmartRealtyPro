/**
 * ArtinSmartRealty V2 - Super Admin Dashboard
 * Platform owner dashboard for managing all tenants
 */

import React, { useState, useEffect } from 'react';
import {
    Users,
    Building2,
    TrendingUp,
    AlertCircle,
    Check,
    X,
    Search,
    MoreHorizontal,
    Clock,
    Ban,
    CheckCircle,
    Bot,
    MessageCircle
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SUBSCRIPTION_COLORS = {
    trial: 'bg-yellow-500',
    active: 'bg-green-500',
    suspended: 'bg-red-500',
    cancelled: 'bg-gray-500',
};

const SuperAdminDashboard = ({ token, onSelectTenant }) => {
    const [tenants, setTenants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [stats, setStats] = useState({
        total: 0,
        active: 0,
        trial: 0,
        suspended: 0,
    });

    useEffect(() => {
        fetchTenants();
    }, []);

    const fetchTenants = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/tenants`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (!response.ok) throw new Error('Failed to fetch tenants');
            
            const data = await response.json();
            setTenants(data);
            
            // Calculate stats
            setStats({
                total: data.length,
                active: data.filter(t => t.subscription_status === 'active').length,
                trial: data.filter(t => t.subscription_status === 'trial').length,
                suspended: data.filter(t => t.subscription_status === 'suspended' || !t.is_active).length,
            });
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const filteredTenants = tenants.filter(t => 
        t.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.email?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
    );

    if (loading) {
        return (
            <div className="min-h-screen bg-navy-900 flex items-center justify-center">
                <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-navy-900 p-8">
            {/* Header */}
            <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                    <div className="p-2 bg-gradient-to-br from-gold-500 to-gold-600 rounded-lg">
                        <Building2 className="text-navy-900" size={24} />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">Super Admin Dashboard</h1>
                        <p className="text-gray-400 text-sm">Platform Management Console</p>
                    </div>
                </div>
            </div>
            
            {/* Error */}
            {error && (
                <div className="bg-red-500/20 border border-red-500 rounded-lg px-4 py-3 mb-6 text-red-400">
                    {error}
                </div>
            )}
            
            {/* Stats Cards */}
            <div className="grid grid-cols-4 gap-6 mb-8">
                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Total Tenants</span>
                        <Users className="text-gold-500" size={20} />
                    </div>
                    <p className="text-3xl font-bold text-white">{stats.total}</p>
                </div>
                
                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Active Subscriptions</span>
                        <CheckCircle className="text-green-500" size={20} />
                    </div>
                    <p className="text-3xl font-bold text-green-500">{stats.active}</p>
                </div>
                
                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">On Trial</span>
                        <Clock className="text-yellow-500" size={20} />
                    </div>
                    <p className="text-3xl font-bold text-yellow-500">{stats.trial}</p>
                </div>
                
                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-gray-400 text-sm">Suspended</span>
                        <Ban className="text-red-500" size={20} />
                    </div>
                    <p className="text-3xl font-bold text-red-500">{stats.suspended}</p>
                </div>
            </div>
            
            {/* Tenants Table */}
            <div className="glass-card rounded-xl overflow-hidden">
                <div className="flex items-center justify-between p-4 border-b border-white/10">
                    <h3 className="text-white font-semibold">All Tenants</h3>
                    
                    <div className="flex items-center gap-4">
                        <div className="flex items-center bg-navy-800 rounded-lg px-4 py-2">
                            <Search size={16} className="text-gray-400 mr-2" />
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                placeholder="Search tenants..."
                                className="bg-transparent text-white text-sm outline-none placeholder-gray-500"
                            />
                        </div>
                    </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead>
                            <tr className="bg-navy-900">
                                {['ID', 'Name', 'Company', 'Email', 'Status', 'Bots', 'Trial Ends', 'Actions'].map(header => (
                                    <th key={header} className="text-gold-500 text-left px-4 py-3 text-sm font-semibold border-b border-white/10">
                                        {header}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTenants.map(tenant => (
                                <tr key={tenant.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                    <td className="text-gray-400 px-4 py-3 text-sm">#{tenant.id}</td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center text-navy-900 font-bold text-sm">
                                                {tenant.name?.charAt(0).toUpperCase() || '?'}
                                            </div>
                                            <span className="text-white text-sm">{tenant.name || 'Unknown'}</span>
                                        </div>
                                    </td>
                                    <td className="text-white px-4 py-3 text-sm">{tenant.company_name || '-'}</td>
                                    <td className="text-white px-4 py-3 text-sm">{tenant.email || '-'}</td>
                                    <td className="px-4 py-3">
                                        <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium text-white ${
                                            tenant.is_active 
                                                ? SUBSCRIPTION_COLORS[tenant.subscription_status] || 'bg-gray-500'
                                                : 'bg-red-500'
                                        }`}>
                                            {tenant.is_active 
                                                ? (tenant.subscription_status || 'trial').toUpperCase()
                                                : 'DISABLED'
                                            }
                                        </span>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            {tenant.telegram_bot_token && (
                                                <span className="flex items-center gap-1 text-blue-400 text-xs bg-blue-500/20 px-2 py-1 rounded">
                                                    <Bot size={12} />
                                                    TG
                                                </span>
                                            )}
                                            {tenant.whatsapp_phone_number_id && (
                                                <span className="flex items-center gap-1 text-green-400 text-xs bg-green-500/20 px-2 py-1 rounded">
                                                    <MessageCircle size={12} />
                                                    WA
                                                </span>
                                            )}
                                            {!tenant.telegram_bot_token && !tenant.whatsapp_phone_number_id && (
                                                <span className="text-gray-500 text-xs">None</span>
                                            )}
                                        </div>
                                    </td>
                                    <td className="text-gray-400 px-4 py-3 text-sm">
                                        {tenant.trial_ends_at 
                                            ? new Date(tenant.trial_ends_at).toLocaleDateString()
                                            : '-'
                                        }
                                    </td>
                                    <td className="px-4 py-3">
                                        <button
                                            onClick={() => onSelectTenant && onSelectTenant(tenant)}
                                            className="text-gold-500 hover:text-gold-400 text-sm font-medium"
                                        >
                                            View Dashboard →
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    
                    {filteredTenants.length === 0 && (
                        <div className="text-center py-12">
                            <p className="text-gray-500">No tenants found</p>
                        </div>
                    )}
                </div>
            </div>
            
            {/* How It Works Section */}
            <div className="glass-card rounded-xl p-6 mt-8">
                <h3 className="text-white font-semibold mb-4">🔐 How Tenant Identification Works</h3>
                <div className="grid grid-cols-3 gap-6 text-sm">
                    <div className="bg-navy-800 rounded-lg p-4">
                        <h4 className="text-gold-500 font-medium mb-2">1. Telegram Bot</h4>
                        <p className="text-gray-400">
                            Each tenant registers their own Telegram bot token. When a message arrives, the webhook URL contains the token, allowing us to identify which tenant owns the bot.
                        </p>
                    </div>
                    <div className="bg-navy-800 rounded-lg p-4">
                        <h4 className="text-gold-500 font-medium mb-2">2. WhatsApp API</h4>
                        <p className="text-gray-400">
                            Each tenant has a unique <code className="text-gold-500">phone_number_id</code> from Meta Business. Incoming messages include this ID, identifying the tenant.
                        </p>
                    </div>
                    <div className="bg-navy-800 rounded-lg p-4">
                        <h4 className="text-gold-500 font-medium mb-2">3. Lead Attribution</h4>
                        <p className="text-gray-400">
                            Every lead is automatically linked to the correct tenant via <code className="text-gold-500">tenant_id</code>. The AI uses tenant-specific data (properties, projects, knowledge) for responses.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SuperAdminDashboard;
