/**
 * Artin Smart Realty V2 - Premium Dashboard
 * Luxury CRM Dashboard with Glassmorphism Design
 * Matching reference: Sidebar + KPI Cards + Pipeline + Scheduling
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Users,
    DollarSign,
    TrendingUp,
    TrendingDown,
    Building2,
    BarChart3,
    MessageSquare,
    Megaphone,
    Gift,
    Settings as SettingsIcon,
    MoreVertical,
    Phone,
    Mail,
    Calendar,
    Percent,
    ArrowUpRight,
} from 'lucide-react';

// Components
import Sidebar from './Sidebar';
import Header from './Header';
import SchedulingCalendar from './SchedulingCalendar';
import RealTimeNotifications, { useNotification } from './RealTimeNotifications';
import Settings from './Settings';
import PropertiesManagement from './PropertiesManagement';
import Analytics from './Analytics';
import Broadcast from './Broadcast';
import Lottery from './Lottery';
import FollowupManagement from './FollowupManagement';
import LeadGeneration from './LeadGeneration';
import LiveChatMonitor from './dashboard/LiveChatMonitor';
import NewsFeed from './NewsFeed';
import KnowledgeBase from './KnowledgeBase';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// ==================== API HELPERS ====================
const getAuthHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`,
});

const api = {
    async get(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },
    async post(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },
    async put(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: getAuthHeaders(),
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },
};

// ==================== KPI CARD COMPONENT ====================
const KPICard = ({ icon: Icon, title, value, subtitle, trend, trendUp, iconBg = 'bg-gold-500/20' }) => (
    <div className="kpi-card glass-card-hover">
        <div className="flex items-start justify-between">
            <div className={`kpi-icon ${iconBg}`}>
                <Icon className="w-6 h-6 text-gold-400" />
            </div>
            {trend && (
                <div className={`flex items-center gap-1 text-xs font-medium ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
                    {trendUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {trend}
                </div>
            )}
        </div>
        <div className="kpi-value">{value}</div>
        <div className="kpi-label">{title}</div>
        {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
    </div>
);

// ==================== LEAD CARD COMPONENT ====================
const LeadCard = ({ lead, onMenuClick }) => {
    const getHotnessClass = (score) => {
        if (score >= 80) return 'hotness-hot';
        if (score >= 50) return 'hotness-warm';
        return 'hotness-cold';
    };

    const getHotnessLabel = (score) => {
        if (score >= 80) return '🔥 Hot';
        if (score >= 50) return '🌡️ Warm';
        return '❄️ Cold';
    };

    const getTimeAgo = (timestamp) => {
        if (!timestamp) return 'Just Now';
        const now = new Date();
        const time = new Date(timestamp);
        const diff = Math.floor((now - time) / 1000 / 60); // minutes

        if (diff < 1) return 'Just Now';
        if (diff < 60) return `${diff}m ago`;
        if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
        return `${Math.floor(diff / 1440)}d ago`;
    };

    return (
        <div className="lead-card group">
            <div className="flex items-start gap-3">
                {/* Avatar */}
                <div className="lead-avatar flex-shrink-0">
                    {lead.name?.charAt(0)?.toUpperCase() || '?'}
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                        <h4 className="lead-name truncate">{lead.name || `Lead #${lead.id}`}</h4>
                        <button
                            onClick={() => onMenuClick?.(lead)}
                            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-navy-600 rounded transition-all"
                        >
                            <MoreVertical className="w-4 h-4 text-gray-400" />
                        </button>
                    </div>

                    <p className="lead-property truncate">
                        {lead.property_type || 'Luxury'} {lead.transaction_type === 'rent' ? 'Rental' : 'Property'} Interest
                        {lead.preferred_location && ` • ${lead.preferred_location}`}
                    </p>

                    <p className="lead-budget">
                        ${lead.budget_min?.toLocaleString() || '0'} - ${lead.budget_max?.toLocaleString() || 'TBD'}
                    </p>
                </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/5">
                <span className={`hotness-badge ${getHotnessClass(lead.lead_score || 0)}`}>
                    {getHotnessLabel(lead.lead_score || 0)}
                </span>
                <span className="lead-time">{getTimeAgo(lead.created_at)}</span>
            </div>
        </div>
    );
};

// ==================== PIPELINE COLUMN COMPONENT ====================
const PipelineColumn = ({ title, count, color, leads, onLeadMenuClick }) => (
    <div className="pipeline-column">
        <div className="pipeline-header">
            <div className="pipeline-title">
                <span className={`w-2 h-2 rounded-full ${color}`} />
                {title}
            </div>
            <span className="pipeline-count">{count}</span>
        </div>

        <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
            {leads.map((lead) => (
                <LeadCard
                    key={lead.id}
                    lead={lead}
                    onMenuClick={onLeadMenuClick}
                />
            ))}

            {leads.length === 0 && (
                <div className="text-center py-8 text-gray-500 text-sm">
                    No leads in this stage
                </div>
            )}
        </div>
    </div>
);

// ==================== MAIN DASHBOARD COMPONENT ====================
const Dashboard = ({ user, onLogout }) => {
    const [activeView, setActiveView] = useState('dashboard');
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [leads, setLeads] = useState([]);
    const [stats, setStats] = useState({
        totalLeads: 0,
        activeDeals: 0,
        conversionRate: 0,
        monthlyRevenue: 0,
        revenueTarget: 500000,
    });
    const [loading, setLoading] = useState(true);

    const { showNotification } = useNotification();

    // Determine user role
    const getUserRole = () => {
        if (user?.is_super_admin) return 'super_admin';
        if (user?.role === 'agent') return 'agent';
        return 'admin';
    };

    // Fetch dashboard data
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const tenantId = user?.tenant_id || localStorage.getItem('tenantId');

                // Fetch leads from the main leads API
                const leadsResponse = await api.get(`/api/v1/tenants/${tenantId}/leads`);
                const leadsData = Array.isArray(leadsResponse) ? leadsResponse : (leadsResponse.leads || []);
                setLeads(leadsData);

                // Try to fetch unified stats for more accurate data
                try {
                    const statsResponse = await api.get(`/api/unified/stats?tenant_id=${tenantId}`);
                    const totalLeads = statsResponse.total_leads || leadsData.length;
                    const activeDeals = (statsResponse.by_status?.qualified || 0) +
                        (statsResponse.by_status?.viewing_scheduled || 0) +
                        (statsResponse.by_status?.negotiating || 0);
                    const closedWon = statsResponse.by_status?.closed_won || 0;
                    const conversionRate = totalLeads > 0 ? ((closedWon / totalLeads) * 100).toFixed(1) : 0;

                    // Calculate revenue from lead budget_max values for closed deals
                    const closedLeads = leadsData.filter(l => l.status === 'closed_won');
                    const monthlyRevenue = closedLeads.reduce((sum, l) => sum + (l.budget_max || 0), 0);

                    setStats({
                        totalLeads,
                        activeDeals,
                        conversionRate,
                        monthlyRevenue,
                        revenueTarget: 500000,
                    });
                } catch (statsError) {
                    // Fallback: calculate from leads data
                    const totalLeads = leadsData.length;
                    const activeDeals = leadsData.filter(l =>
                        ['qualified', 'viewing_scheduled', 'negotiating'].includes(l.status)
                    ).length;
                    const closedWon = leadsData.filter(l => l.status === 'closed_won').length;
                    const conversionRate = totalLeads > 0 ? ((closedWon / totalLeads) * 100).toFixed(1) : 0;
                    const closedLeads = leadsData.filter(l => l.status === 'closed_won');
                    const monthlyRevenue = closedLeads.reduce((sum, l) => sum + (l.budget_max || 0), 0);

                    setStats({
                        totalLeads,
                        activeDeals,
                        conversionRate,
                        monthlyRevenue,
                        revenueTarget: 500000,
                    });
                }

            } catch (error) {
                console.error('Error fetching dashboard data:', error);
                // Set empty state instead of mock data
                setLeads([]);
                setStats({
                    totalLeads: 0,
                    activeDeals: 0,
                    conversionRate: 0,
                    monthlyRevenue: 0,
                    revenueTarget: 500000,
                });
                showNotification?.('Failed to load dashboard data', 'error');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [user]);

    // Group leads by status for pipeline
    const pipelineData = {
        new: leads.filter(l => l.status === 'new' || !l.status),
        qualified: leads.filter(l => l.status === 'qualified' || l.status === 'contacted'),
        viewing_scheduled: leads.filter(l => l.status === 'viewing_scheduled' || l.status === 'negotiating'),
        closed: leads.filter(l => l.status === 'closed_won' || l.status === 'closed_lost'),
    };

    // Handle lead menu actions
    const handleLeadMenuClick = (lead) => {
        // TODO: Implement lead action menu
        console.log('Lead menu clicked:', lead);
    };

    // Render content based on active view
    const renderContent = () => {
        switch (activeView) {
            case 'settings':
                return <Settings tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'properties':
                return <PropertiesManagement tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'analytics':
                return <Analytics tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'broadcast':
                return <Broadcast tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'lottery':
                return <Lottery tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'live-chat':
                return <LiveChatMonitor tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'lead-gen':
                return <LeadGeneration tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'followup':
                return <FollowupManagement tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'news':
                return <NewsFeed tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'knowledge-base':
                return <KnowledgeBase tenantId={user?.tenant_id} token={localStorage.getItem('token')} />;
            case 'calendar':
                return (
                    <div className="p-6">
                        <h2 className="text-2xl font-bold text-white mb-6">Calendar & Scheduling</h2>
                        <div className="max-w-md">
                            <SchedulingCalendar tenantId={user?.tenant_id} token={localStorage.getItem('token')} />
                        </div>
                    </div>
                );
            case 'pipeline':
                return (
                    <div className="p-6">
                        <h2 className="text-2xl font-bold text-white mb-6">Lead Pipeline</h2>
                        <div className="pipeline-container">
                            <div className="flex gap-6 overflow-x-auto pb-4">
                                <PipelineColumn
                                    title="New Leads"
                                    count={pipelineData.new.length}
                                    color="bg-blue-500"
                                    leads={pipelineData.new}
                                    onLeadMenuClick={handleLeadMenuClick}
                                />
                                <PipelineColumn
                                    title="Qualified"
                                    count={pipelineData.qualified.length}
                                    color="bg-yellow-500"
                                    leads={pipelineData.qualified}
                                    onLeadMenuClick={handleLeadMenuClick}
                                />
                                <PipelineColumn
                                    title="Viewing Scheduled"
                                    count={pipelineData.viewing_scheduled.length}
                                    color="bg-orange-500"
                                    leads={pipelineData.viewing_scheduled}
                                    onLeadMenuClick={handleLeadMenuClick}
                                />
                                <PipelineColumn
                                    title="Closed"
                                    count={pipelineData.closed.length}
                                    color="bg-green-500"
                                    leads={pipelineData.closed}
                                    onLeadMenuClick={handleLeadMenuClick}
                                />
                            </div>
                        </div>
                    </div>
                );
            default:
                // Main Dashboard View
                return (
                    <div className="flex-1 overflow-y-auto">
                        {/* Main Content Area */}
                        <div className="p-6">
                            {/* KPI Cards */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
                                <KPICard
                                    icon={Users}
                                    title="Total Leads"
                                    value={stats.totalLeads.toLocaleString()}
                                    trend="+12% this month"
                                    trendUp={true}
                                />
                                <KPICard
                                    icon={Building2}
                                    title="Active Deals"
                                    value={stats.activeDeals.toString()}
                                    subtitle={`${Math.round(stats.activeDeals * 0.6)} pending closing`}
                                />
                                <KPICard
                                    icon={Percent}
                                    title="Conversion Rate"
                                    value={`${stats.conversionRate}%`}
                                    trend="+0.5%"
                                    trendUp={true}
                                />
                                <KPICard
                                    icon={DollarSign}
                                    title="Monthly Revenue"
                                    value={`$${(stats.monthlyRevenue / 1000).toFixed(0)}k`}
                                    subtitle={`Target: $${(stats.revenueTarget / 1000).toFixed(0)}k`}
                                />
                            </div>

                            {/* Pipeline Section */}
                            <div className="pipeline-container mb-6">
                                <div className="flex items-center justify-between mb-6">
                                    <h3 className="text-lg font-semibold text-white">The Pipeline</h3>
                                    <button
                                        onClick={() => setActiveView('pipeline')}
                                        className="text-sm text-gold-400 hover:text-gold-300 flex items-center gap-1"
                                    >
                                        View All <ArrowUpRight className="w-4 h-4" />
                                    </button>
                                </div>

                                <div className="flex gap-6 overflow-x-auto pb-4">
                                    <PipelineColumn
                                        title="New Leads"
                                        count={pipelineData.new.length}
                                        color="bg-blue-500"
                                        leads={pipelineData.new.slice(0, 3)}
                                        onLeadMenuClick={handleLeadMenuClick}
                                    />
                                    <PipelineColumn
                                        title="Qualified"
                                        count={pipelineData.qualified.length}
                                        color="bg-yellow-500"
                                        leads={pipelineData.qualified.slice(0, 3)}
                                        onLeadMenuClick={handleLeadMenuClick}
                                    />
                                    <PipelineColumn
                                        title="Viewing Scheduled"
                                        count={pipelineData.viewing_scheduled.length}
                                        color="bg-orange-500"
                                        leads={pipelineData.viewing_scheduled.slice(0, 3)}
                                        onLeadMenuClick={handleLeadMenuClick}
                                    />
                                    <PipelineColumn
                                        title="Closed"
                                        count={pipelineData.closed.length}
                                        color="bg-green-500"
                                        leads={pipelineData.closed.slice(0, 3)}
                                        onLeadMenuClick={handleLeadMenuClick}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                );
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-navy flex items-center justify-center">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <RealTimeNotifications>
            <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 flex">
                {/* Sidebar */}
                <Sidebar
                    activeView={activeView}
                    onViewChange={setActiveView}
                    user={user}
                    onLogout={onLogout}
                    isCollapsed={sidebarCollapsed}
                    onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
                    userRole={getUserRole()}
                />

                {/* Main Content */}
                <div className="flex-1 flex flex-col min-h-screen overflow-hidden">
                    {/* Header */}
                    <Header
                        user={user}
                        onLogout={onLogout}
                    />

                    {/* Content Area with Scheduling Sidebar */}
                    <div className="flex-1 flex overflow-hidden">
                        {/* Main Content */}
                        <div className="flex-1 overflow-y-auto">
                            {renderContent()}
                        </div>

                        {/* Scheduling Panel - Only show on dashboard view */}
                        {activeView === 'dashboard' && (
                            <div className="hidden xl:block w-80 border-l border-white/5 p-4 overflow-y-auto">
                                <SchedulingCalendar
                                    tenantId={user?.tenant_id}
                                    token={localStorage.getItem('token')}
                                />
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </RealTimeNotifications>
    );
};

export default Dashboard;
