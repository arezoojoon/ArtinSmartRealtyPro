/**
 * ArtinSmartRealty V2 - Super Dashboard
 * Modern B2B SaaS Dashboard for Real Estate Agents
 * Dark Mode Theme with Luxury Aesthetics & Glassmorphism
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    LayoutDashboard,
    KanbanSquare,
    CalendarDays,
    Building2,
    BarChart3,
    Settings,
    Search,
    Bell,
    Users,
    Briefcase,
    Percent,
    DollarSign,
    Plus,
    MoreHorizontal,
    TrendingUp,
    TrendingDown,
    Home,
    X,
    Download
} from 'lucide-react';

// ==================== CONSTANTS ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const STATUS_COLORS = {
  new: 'bg-red-500',
  contacted: 'bg-orange-500',
  qualified: 'bg-yellow-500',
  viewing_scheduled: 'bg-green-500',
  negotiating: 'bg-blue-500',
  closed_won: 'bg-green-500',
  closed_lost: 'bg-gray-500',
};

const PURPOSE_LABELS = {
  investment: '📈 Investment',
  living: '🏡 Living',
  residency: '🛂 Residency/Visa',
};

const DAYS_OF_WEEK = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

// ==================== API HELPERS ====================

const api = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`);
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
  
  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { method: 'DELETE' });
    if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
    return response.json();
  },
};

// ==================== COMPONENTS ====================

// کامپوننت کارت KPI شیشهای
const KpiCard = ({ title, value, trend, icon: Icon, trendUp }) => (
    <div className="glass-card rounded-xl p-6 relative overflow-hidden">
        {/* نوار طلایی بالای کارت */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-gold-500 to-gold-400"></div>
        
        <div className="flex justify-between items-start">
            <div>
                <p className="text-gray-400 text-sm mb-1">{title}</p>
                <h3 className="text-3xl font-bold text-white">{value}</h3>
                {trend && (
                    <div className={`flex items-center mt-2 text-xs ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
                        {trendUp ? <TrendingUp size={14} className="mr-1" /> : <TrendingDown size={14} className="mr-1" />}
                        <span>{trend}</span>
                    </div>
                )}
            </div>
            <div className="p-3 bg-navy-800/50 rounded-lg">
                <Icon className="text-gold-500" size={28} />
            </div>
        </div>
    </div>
);

// کامپوننت آیتمهای سایدبار
const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
    <button
        onClick={onClick}
        className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
            active 
                ? 'bg-navy-800 text-gold-500 border-l-2 border-gold-500' 
                : 'text-gray-400 hover:bg-navy-800/50 hover:text-white'
        }`}
    >
        <Icon size={20} />
        <span className="font-medium">{label}</span>
    </button>
);

// کامپوننت کارت لید در پایپلاین
const LeadCard = ({ name, phone, budget, purpose, onClick }) => (
    <div 
        onClick={onClick}
        className="bg-navy-900 rounded-lg p-4 cursor-pointer border border-white/5 hover:border-gold-500/30 transition-all hover:-translate-y-1"
    >
        <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center text-navy-900 font-bold">
                {name ? name.charAt(0).toUpperCase() : '?'}
            </div>
            <div>
                <h4 className="text-white font-medium text-sm">{name || 'Anonymous'}</h4>
                <p className="text-gray-500 text-xs">{phone || 'No phone'}</p>
            </div>
        </div>
        {budget && (
            <p className="text-gold-500 text-sm mb-2">💰 Up to AED {(budget / 1000000).toFixed(1)}M</p>
        )}
        {purpose && (
            <span className="inline-block bg-navy-800 text-gray-300 text-xs px-2 py-1 rounded">
                {PURPOSE_LABELS[purpose] || purpose}
            </span>
        )}
    </div>
);

// Lead Pipeline Kanban Column
const PipelineColumn = ({ title, leads, colorClass, onLeadClick }) => (
    <div className="flex-1 min-w-[260px] bg-navy-800/50 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold text-sm">{title}</h3>
            <span className={`${colorClass} text-white text-xs px-3 py-1 rounded-full font-semibold`}>
                {leads.length}
            </span>
        </div>
        <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {leads.map(lead => (
                <LeadCard
                    key={lead.id}
                    name={lead.name}
                    phone={lead.phone}
                    budget={lead.budget_max}
                    purpose={lead.purpose}
                    onClick={() => onLeadClick(lead)}
                />
            ))}
            {leads.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-8">No leads in this stage</p>
            )}
        </div>
    </div>
);

// Weekly Calendar for Scheduling
const WeeklyCalendar = ({ slots, onAddSlot, onDeleteSlot }) => {
    const [showModal, setShowModal] = useState(false);
    const [selectedDay, setSelectedDay] = useState(DAYS_OF_WEEK[0]);
    const [newSlot, setNewSlot] = useState({ start_time: '09:00', end_time: '10:00' });

    const handleAddSlot = () => {
        onAddSlot({
            day_of_week: selectedDay,
            start_time: newSlot.start_time,
            end_time: newSlot.end_time,
        });
        setShowModal(false);
        setNewSlot({ start_time: '09:00', end_time: '10:00' });
    };

    return (
        <div className="glass-card rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-white font-semibold flex items-center gap-2">
                    <CalendarDays size={20} className="text-gold-500" />
                    Weekly Availability
                </h3>
                <button
                    onClick={() => setShowModal(true)}
                    className="flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 px-4 py-2 rounded-lg font-semibold text-sm transition-colors"
                >
                    <Plus size={16} />
                    Set Availability
                </button>
            </div>

            <div className="grid grid-cols-7 gap-3">
                {DAYS_OF_WEEK.map((day, index) => {
                    const daySlots = slots.filter(s => s.day_of_week === day);
                    return (
                        <div key={day} className="bg-navy-900 rounded-lg p-3 min-h-[140px]">
                            <p className="text-gold-500 text-xs font-semibold text-center mb-3">
                                {DAY_LABELS[index]}
                            </p>
                            {daySlots.map(slot => (
                                <div
                                    key={slot.id}
                                    className={`${slot.is_booked ? 'bg-red-500/20 text-red-400' : 'bg-gold-500 text-navy-900'} rounded px-2 py-1 text-xs mb-2 flex justify-between items-center`}
                                >
                                    <span>{slot.start_time} - {slot.end_time}</span>
                                    {!slot.is_booked && (
                                        <button onClick={() => onDeleteSlot(slot.id)} className="hover:opacity-70">
                                            <X size={12} />
                                        </button>
                                    )}
                                </div>
                            ))}
                            {daySlots.length === 0 && (
                                <p className="text-gray-600 text-xs text-center">No slots</p>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Add Slot Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
                    <div className="bg-navy-900 rounded-xl p-6 w-80 border border-gold-500/30">
                        <h3 className="text-white font-semibold mb-4">Add Available Slot</h3>
                        
                        <label className="text-gray-400 text-sm block mb-2">Day of Week</label>
                        <select
                            value={selectedDay}
                            onChange={e => setSelectedDay(e.target.value)}
                            className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 mb-4 border border-white/10 focus:border-gold-500 outline-none"
                        >
                            {DAYS_OF_WEEK.map((day, i) => (
                                <option key={day} value={day}>{DAY_LABELS[i]}</option>
                            ))}
                        </select>
                        
                        <div className="flex gap-3 mb-6">
                            <div className="flex-1">
                                <label className="text-gray-400 text-sm block mb-2">Start Time</label>
                                <input
                                    type="time"
                                    value={newSlot.start_time}
                                    onChange={e => setNewSlot({ ...newSlot, start_time: e.target.value })}
                                    className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/10 focus:border-gold-500 outline-none"
                                />
                            </div>
                            <div className="flex-1">
                                <label className="text-gray-400 text-sm block mb-2">End Time</label>
                                <input
                                    type="time"
                                    value={newSlot.end_time}
                                    onChange={e => setNewSlot({ ...newSlot, end_time: e.target.value })}
                                    className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/10 focus:border-gold-500 outline-none"
                                />
                            </div>
                        </div>
                        
                        <div className="flex gap-3">
                            <button
                                onClick={() => setShowModal(false)}
                                className="flex-1 px-4 py-2 rounded-lg border border-white/10 text-white hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAddSlot}
                                className="flex-1 px-4 py-2 rounded-lg bg-gold-500 text-navy-900 font-semibold hover:bg-gold-400 transition-colors"
                            >
                                Add Slot
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// Lead Table
const LeadTable = ({ leads, onExport }) => (
    <div className="glass-card rounded-xl overflow-hidden">
        <div className="flex justify-between items-center p-4 border-b border-white/10">
            <h3 className="text-white font-semibold">Lead Manager</h3>
            <button
                onClick={onExport}
                className="flex items-center gap-2 bg-green-500 hover:bg-green-400 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors"
            >
                <Download size={16} />
                Export to Excel
            </button>
        </div>
        
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="bg-navy-900">
                        {['Name', 'Phone', 'Budget', 'Purpose', 'Payment', 'Status', 'Voice Transcript'].map(header => (
                            <th key={header} className="text-gold-500 text-left px-4 py-3 text-sm font-semibold border-b border-white/10">
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {leads.map(lead => (
                        <tr key={lead.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="text-white px-4 py-3 text-sm">{lead.name || 'Anonymous'}</td>
                            <td className="text-white px-4 py-3 text-sm">{lead.phone || '-'}</td>
                            <td className="text-gold-500 px-4 py-3 text-sm">
                                {lead.budget_min || lead.budget_max 
                                    ? `${lead.budget_min ? `${(lead.budget_min/1000000).toFixed(1)}M` : ''} - ${lead.budget_max ? `${(lead.budget_max/1000000).toFixed(1)}M` : ''}`
                                    : '-'}
                            </td>
                            <td className="px-4 py-3">
                                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                                    lead.purpose === 'residency' ? 'bg-gold-500 text-navy-900' : 'bg-navy-800 text-white'
                                }`}>
                                    {PURPOSE_LABELS[lead.purpose] || lead.purpose || '-'}
                                </span>
                            </td>
                            <td className="text-white px-4 py-3 text-sm capitalize">{lead.payment_method || '-'}</td>
                            <td className="px-4 py-3">
                                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium text-white ${STATUS_COLORS[lead.status] || 'bg-gray-500'}`}>
                                    {lead.status?.replace('_', ' ') || 'new'}
                                </span>
                            </td>
                            <td className="text-gray-400 px-4 py-3 text-xs max-w-[200px] truncate">
                                {lead.voice_transcript || '-'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            {leads.length === 0 && (
                <div className="text-center py-12">
                    <p className="text-gray-500">No leads yet. Start your Telegram bot to capture leads!</p>
                </div>
            )}
        </div>
    </div>
);

// ==================== MAIN DASHBOARD COMPONENT ====================

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [tenantId] = useState(1);
    const [stats, setStats] = useState(null);
    const [leads, setLeads] = useState([]);
    const [slots, setSlots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchDashboardData = useCallback(async () => {
        try {
            setLoading(true);
            const [statsData, leadsData, slotsData] = await Promise.all([
                api.get(`/api/tenants/${tenantId}/dashboard/stats`),
                api.get(`/api/tenants/${tenantId}/leads`),
                api.get(`/api/tenants/${tenantId}/schedule`),
            ]);
            setStats(statsData);
            setLeads(leadsData);
            setSlots(slotsData);
            setError(null);
        } catch (err) {
            console.error('Failed to fetch dashboard data:', err);
            setError('Failed to load dashboard data. Please try again.');
        } finally {
            setLoading(false);
        }
    }, [tenantId]);

    useEffect(() => {
        fetchDashboardData();
    }, [fetchDashboardData]);

    const handleAddSlot = async (slotData) => {
        try {
            await api.post(`/api/tenants/${tenantId}/schedule`, slotData);
            fetchDashboardData();
        } catch (err) {
            console.error('Failed to add slot:', err);
            alert('Failed to add slot. Check for time conflicts.');
        }
    };

    const handleDeleteSlot = async (slotId) => {
        try {
            await api.delete(`/api/tenants/${tenantId}/schedule/${slotId}`);
            fetchDashboardData();
        } catch (err) {
            console.error('Failed to delete slot:', err);
            alert('Failed to delete slot.');
        }
    };

    const handleExportLeads = () => {
        window.open(`${API_BASE_URL}/api/tenants/${tenantId}/leads/export`, '_blank');
    };

    const handleLeadClick = (lead) => {
        console.log('Lead clicked:', lead);
        setActiveTab('leads');
    };

    const leadsByStatus = {
        new: leads.filter(l => l.status === 'new' || !l.status),
        qualified: leads.filter(l => l.status === 'qualified'),
        viewing_scheduled: leads.filter(l => l.status === 'viewing_scheduled'),
        closed: leads.filter(l => l.status === 'closed_won' || l.status === 'closed_lost'),
    };

    const sidebarItems = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
        { id: 'leads', icon: KanbanSquare, label: 'Lead Pipeline' },
        { id: 'calendar', icon: CalendarDays, label: 'Calendar' },
        { id: 'properties', icon: Building2, label: 'Properties' },
        { id: 'analytics', icon: BarChart3, label: 'Analytics' },
        { id: 'settings', icon: Settings, label: 'Settings' },
    ];

    if (loading) {
        return (
            <div className="min-h-screen bg-navy-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-navy-900 flex font-sans">
            {/* Sidebar */}
            <aside className="w-64 bg-navy-900 border-r border-white/10 p-4 flex flex-col">
                {/* Logo */}
                <div className="mb-8 pb-6 border-b border-white/10">
                    <h1 className="text-gold-500 text-xl font-bold">ArtinSmartRealty</h1>
                    <p className="text-gray-500 text-xs mt-1">Real Estate SaaS v2.0</p>
                </div>

                {/* Navigation */}
                <nav className="flex-1 space-y-2">
                    {sidebarItems.map(item => (
                        <SidebarItem
                            key={item.id}
                            icon={item.icon}
                            label={item.label}
                            active={activeTab === item.id}
                            onClick={() => setActiveTab(item.id)}
                        />
                    ))}
                </nav>

                {/* User Profile */}
                <div className="pt-4 border-t border-white/10 flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center text-navy-900 font-bold">
                        A
                    </div>
                    <div>
                        <p className="text-white text-sm font-medium">Agent</p>
                        <p className="text-green-400 text-xs flex items-center gap-1">
                            <span className="w-2 h-2 bg-green-400 rounded-full"></span>
                            Online
                        </p>
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <div className="flex-1 flex flex-col">
                {/* Header */}
                <header className="bg-navy-900 border-b border-white/10 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center bg-navy-800 rounded-lg px-4 py-2 w-80">
                        <Search size={18} className="text-gray-400 mr-3" />
                        <input
                            type="text"
                            placeholder="Search leads, properties..."
                            className="bg-transparent text-white text-sm outline-none w-full placeholder-gray-500"
                        />
                    </div>

                    <div className="flex items-center gap-4">
                        <button className="relative p-2 text-gray-400 hover:text-white transition-colors">
                            <Bell size={22} />
                            <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs w-5 h-5 rounded-full flex items-center justify-center font-semibold">
                                3
                            </span>
                        </button>
                        <div className="w-10 h-10 rounded-full border-2 border-gold-500 overflow-hidden">
                            <img
                                src="https://ui-avatars.com/api/?name=Agent&background=D4AF37&color=0f1729&bold=true"
                                alt="Profile"
                                className="w-full h-full object-cover"
                            />
                        </div>
                    </div>
                </header>

                {/* Main Area */}
                <main className="flex-1 p-6 overflow-y-auto">
                    {error && (
                        <div className="bg-red-500/20 border border-red-500 rounded-lg px-4 py-3 mb-6 text-red-400">
                            {error}
                        </div>
                    )}

                    {/* Dashboard Tab */}
                    {activeTab === 'dashboard' && stats && (
                        <>
                            {/* KPI Cards */}
                            <div className="grid grid-cols-4 gap-6 mb-8">
                                <KpiCard
                                    title="Total Leads"
                                    value={stats.total_leads}
                                    icon={Users}
                                    trend="+12% from last month"
                                    trendUp={true}
                                />
                                <KpiCard
                                    title="Active Deals"
                                    value={stats.active_deals}
                                    icon={Briefcase}
                                    trend="+5% from last week"
                                    trendUp={true}
                                />
                                <KpiCard
                                    title="Conversion Rate"
                                    value={`${stats.conversion_rate}%`}
                                    icon={Percent}
                                    trend="+2.3% improvement"
                                    trendUp={true}
                                />
                                <KpiCard
                                    title="Scheduled Viewings"
                                    value={stats.scheduled_viewings}
                                    icon={Home}
                                />
                            </div>

                            {/* Pipeline View */}
                            <h2 className="text-white text-lg font-semibold mb-4">Lead Pipeline</h2>
                            <div className="flex gap-4 mb-8 overflow-x-auto pb-4">
                                <PipelineColumn
                                    title="New Leads"
                                    leads={leadsByStatus.new}
                                    colorClass="bg-red-500"
                                    onLeadClick={handleLeadClick}
                                />
                                <PipelineColumn
                                    title="Qualified"
                                    leads={leadsByStatus.qualified}
                                    colorClass="bg-yellow-500"
                                    onLeadClick={handleLeadClick}
                                />
                                <PipelineColumn
                                    title="Viewing Scheduled"
                                    leads={leadsByStatus.viewing_scheduled}
                                    colorClass="bg-green-500"
                                    onLeadClick={handleLeadClick}
                                />
                                <PipelineColumn
                                    title="Closed"
                                    leads={leadsByStatus.closed}
                                    colorClass="bg-gray-500"
                                    onLeadClick={handleLeadClick}
                                />
                            </div>

                            {/* Calendar Widget */}
                            <WeeklyCalendar
                                slots={slots}
                                onAddSlot={handleAddSlot}
                                onDeleteSlot={handleDeleteSlot}
                            />
                        </>
                    )}

                    {/* Leads Tab */}
                    {activeTab === 'leads' && (
                        <LeadTable leads={leads} onExport={handleExportLeads} />
                    )}

                    {/* Calendar Tab */}
                    {activeTab === 'calendar' && (
                        <WeeklyCalendar
                            slots={slots}
                            onAddSlot={handleAddSlot}
                            onDeleteSlot={handleDeleteSlot}
                        />
                    )}

                    {/* Placeholder for other tabs */}
                    {['properties', 'analytics', 'settings'].includes(activeTab) && (
                        <div className="glass-card rounded-xl h-96 flex items-center justify-center">
                            <div className="text-center">
                                <div className="text-5xl mb-4">🚧</div>
                                <p className="text-gray-400">
                                    {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} module coming soon!
                                </p>
                            </div>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
};

export default Dashboard;
