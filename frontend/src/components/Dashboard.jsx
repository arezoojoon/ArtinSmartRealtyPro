/**
 * Artin Smart Realty V2 - Super Dashboard
 * Modern B2B SaaS Dashboard with Glassmorphism Design System
 * Refactored with Layout, Sidebar, and Header Components
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    Users,
    Briefcase,
    Percent,
    Home,
    Plus,
    TrendingUp,
    TrendingDown,
    X,
    Download,
    CalendarDays
} from 'lucide-react';
import { Layout } from './Layout';
import SettingsPage from './Settings';
import PropertiesManagement from './PropertiesManagement';
import Analytics from './Analytics';
import QRGenerator from './QRGenerator';
import Broadcast from './Broadcast';
import Catalogs from './Catalogs';
import Lottery from './Lottery';

// ==================== CONSTANTS ====================

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

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

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const api = {
  async get(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) {
      if (response.status === 401) {
        // Token expired, redirect to login
        localStorage.clear();
        window.location.reload();
      }
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  },
  
  async post(endpoint, data) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        ...getAuthHeaders()
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.clear();
        window.location.reload();
      }
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  },
  
  async delete(endpoint) {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, { 
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!response.ok) {
      if (response.status === 401) {
        localStorage.clear();
        window.location.reload();
      }
      throw new Error(`API Error: ${response.statusText}`);
    }
    return response.json();
  },
};

// ==================== COMPONENTS ====================

// KPI Card Component with Glassmorphism
const KpiCard = ({ title, value, trend, icon: Icon, trendUp, color = 'gold' }) => (
    <div className="glass-card glass-card-hover rounded-2xl p-6 relative overflow-hidden group">
        <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity bg-${color}-500 rounded-bl-2xl`}>
            <Icon size={48} />
        </div>
        <p className="text-gray-400 text-sm uppercase tracking-wide mb-1">{title}</p>
        <h3 className="text-3xl font-bold text-white mt-2">{value}</h3>
        {trend && (
            <div className={`flex items-center mt-3 text-xs ${trendUp ? 'text-green-400' : 'text-red-400'}`}>
                {trendUp ? <TrendingUp size={14} className="mr-1" /> : <TrendingDown size={14} className="mr-1" />}
                <span>{trend}</span>
            </div>
        )}
    </div>
);

// Lead Card Component with Glass Effect
const LeadCard = ({ name, phone, budget, purpose, onClick }) => (
    <div 
        onClick={onClick}
        className="glass-card glass-card-hover rounded-xl p-4 cursor-pointer"
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

// Lead Pipeline Kanban Column with Glass Design
const PipelineColumn = ({ title, leads, colorClass, onLeadClick }) => (
    <div className="flex-1 min-w-[280px] glass-card rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-semibold">{title}</h3>
            <span className={`${colorClass} text-white text-xs px-3 py-1.5 rounded-full font-bold`}>
                {leads.length}
            </span>
        </div>
        <div className="space-y-3 max-h-[450px] overflow-y-auto pr-2">
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

// Weekly Calendar Component with Glassmorphism
const WeeklyCalendar = ({ slots, onAddSlot, onDeleteSlot, compactMode = false, onOpenFullCalendar }) => {
    const [showModal, setShowModal] = useState(false);
    const [selectedDay, setSelectedDay] = useState(DAYS_OF_WEEK[0]);
    const [newSlot, setNewSlot] = useState({ start_time: '09:00', end_time: '10:00' });

    // Calculate current week dates
    const getWeekDates = () => {
        const today = new Date();
        const currentDay = today.getDay(); // 0 = Sunday, 1 = Monday, etc.
        const monday = new Date(today);
        
        // Calculate Monday of current week
        const daysFromMonday = currentDay === 0 ? 6 : currentDay - 1;
        monday.setDate(today.getDate() - daysFromMonday);
        
        return DAYS_OF_WEEK.map((_, index) => {
            const date = new Date(monday);
            date.setDate(monday.getDate() + index);
            return {
                dayName: DAY_LABELS[index],
                date: date,
                formatted: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            };
        });
    };

    const weekDates = getWeekDates();

    const handleAddSlot = () => {
        onAddSlot({
            day_of_week: selectedDay,
            start_time: newSlot.start_time,
            end_time: newSlot.end_time,
        });
        setShowModal(false);
        setNewSlot({ start_time: '09:00', end_time: '10:00' });
    };

    const handleSetAvailability = () => {
        if (compactMode && onOpenFullCalendar) {
            // در حالت compact، به جای باز کردن modal، به تب Calendar برو
            onOpenFullCalendar();
        } else {
            // در حالت عادی، modal را باز کن
            setShowModal(true);
        }
    };

    return (
        <div className="glass-card rounded-2xl p-6">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-white font-semibold text-lg flex items-center gap-2">
                    <CalendarDays size={20} className="text-gold-500" />
                    {compactMode ? 'وقت‌های خالی شما' : 'Weekly Availability'}
                </h3>
                <button
                    onClick={handleSetAvailability}
                    className="btn-gold flex items-center gap-2"
                >
                    <Plus size={16} />
                    {compactMode ? '🗓️ مدیریت تقویم' : 'Set Availability'}
                </button>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-7 gap-3">
                {DAYS_OF_WEEK.map((day, index) => {
                    const daySlots = slots.filter(s => s.day_of_week === day);
                    const dayInfo = weekDates[index];
                    return (
                        <div key={day} className="glass-card rounded-xl p-3 min-h-[140px]">
                            <p className="text-gold-500 text-xs font-bold text-center mb-1 uppercase">
                                {dayInfo.dayName}
                            </p>
                            <p className="text-gray-400 text-xs text-center mb-3">
                                {dayInfo.formatted}
                            </p>
                            {daySlots.map(slot => (
                                <div
                                    key={slot.id}
                                    className={`${slot.is_booked ? 'badge-red' : 'bg-gold-500 text-navy-900'} rounded-lg px-2 py-1.5 text-xs mb-2 flex justify-between items-center font-medium`}
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
                <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="glass-card rounded-2xl p-6 w-96 border-2 border-gold-500/30">
                        <h3 className="text-white font-bold text-lg mb-4">Add Available Slot</h3>
                        
                        <label className="text-gray-400 text-sm block mb-2">Day of Week</label>
                        <select
                            value={selectedDay}
                            onChange={e => setSelectedDay(e.target.value)}
                            className="w-full bg-navy-800 text-white rounded-lg px-3 py-2.5 mb-4 border border-white/10 focus:border-gold-500 outline-none"
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
// Lead Table Component with Glassmorphism
const LeadTable = ({ leads, onExport }) => (
    <div className="glass-card rounded-2xl overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b border-white/10">
            <h3 className="text-white font-bold text-lg">Lead Manager</h3>
            <button
                onClick={onExport}
                className="btn-gold flex items-center gap-2"
            >
                <Download size={16} />
                Export to Excel
            </button>
        </div>
        
        <div className="overflow-x-auto">
            <table className="w-full">
                <thead>
                    <tr className="bg-navy-900/50">
                        {['Name', 'Phone', 'Budget', 'Purpose', 'Payment', 'Status', 'Voice Transcript'].map(header => (
                            <th key={header} className="text-gold-500 text-left px-6 py-4 text-sm font-bold border-b border-white/10 uppercase tracking-wide">
                                {header}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {leads.map(lead => (
                        <tr key={lead.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            <td className="text-white px-6 py-4 text-sm font-medium">{lead.name || 'Anonymous'}</td>
                            <td className="text-white px-6 py-4 text-sm">{lead.phone || '-'}</td>
                            <td className="text-gold-500 px-6 py-4 text-sm font-semibold">
                                {lead.budget_min || lead.budget_max 
                                    ? `${lead.budget_min ? `${(lead.budget_min/1000000).toFixed(1)}M` : ''} - ${lead.budget_max ? `${(lead.budget_max/1000000).toFixed(1)}M` : ''}`
                                    : '-'}
                            </td>
                            <td className="px-6 py-4">
                                <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold ${
                                    lead.purpose === 'residency' ? 'badge-gold' : 'badge-blue'
                                }`}>
                                    {PURPOSE_LABELS[lead.purpose] || lead.purpose || '-'}
                                </span>
                            </td>
                            <td className="text-white px-6 py-4 text-sm capitalize">{lead.payment_method || '-'}</td>
                            <td className="px-6 py-4">
                                <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-bold text-white ${STATUS_COLORS[lead.status] || 'bg-gray-500'}`}>
                                    {lead.status?.replace('_', ' ') || 'new'}
                                </span>
                            </td>
                            <td className="text-gray-400 px-6 py-4 text-xs max-w-[250px] truncate">
                                {lead.voice_transcript || '-'}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            
            {leads.length === 0 && (
                <div className="text-center py-16">
                    <p className="text-gray-500 text-lg">No leads yet. Start your Telegram bot to capture leads!</p>
                </div>
            )}
        </div>
    </div>
);

// ==================== MAIN DASHBOARD COMPONENT ====================

const Dashboard = ({ user, onLogout }) => {
    const [activeTab, setActiveTab] = useState('dashboard');
    const tenantId = user?.tenant_id || parseInt(localStorage.getItem('tenantId')) || 1;
    const token = user?.token || localStorage.getItem('token');
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
            // Get existing slots and add the new one
            const allSlots = [...slots, slotData];
            
            // Backend expects { "slots": [array] } format
            await api.post(`/api/tenants/${tenantId}/schedule`, {
                slots: allSlots
            });
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

    if (loading) {
        return (
            <div className="min-h-screen bg-navy-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-400 text-lg">Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <Layout activeTab={activeTab} setActiveTab={setActiveTab} user={user} onLogout={onLogout}>
            {error && (
                <div className="glass-card border-2 border-red-500/50 bg-red-500/10 rounded-xl px-6 py-4 mb-6 text-red-400 animate-fade-in">
                    ⚠️ {error}
                </div>
            )}

            {/* Dashboard Overview Tab */}
            {activeTab === 'dashboard' && stats && (
                <div className="space-y-8 animate-fade-in">
                    {/* Header */}
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2">Dashboard Overview</h1>
                        <p className="text-gray-400">Welcome back, {user?.name || 'Agent'}</p>
                    </div>

                    {/* KPI Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <KpiCard
                            title="Total Leads"
                            value={stats.total_leads}
                            icon={Users}
                            trend="+12% from last month"
                            trendUp={true}
                            color="gold"
                        />
                        <KpiCard
                            title="Active Deals"
                            value={stats.active_deals}
                            icon={Briefcase}
                            trend="+5% from last week"
                            trendUp={true}
                            color="green"
                        />
                        <KpiCard
                            title="Conversion Rate"
                            value={`${stats.conversion_rate}%`}
                            icon={Percent}
                            trend="+2.3% improvement"
                            trendUp={true}
                            color="blue"
                        />
                        <KpiCard
                            title="Scheduled Viewings"
                            value={stats.scheduled_viewings}
                            icon={Home}
                            color="purple"
                        />
                    </div>

                    {/* Pipeline Kanban */}
                    <div>
                        <h2 className="text-white text-xl font-bold mb-6 flex items-center gap-2">
                            <div className="w-1 h-6 bg-gold-500 rounded"></div>
                            Lead Pipeline
                        </h2>
                        <div className="overflow-x-auto pb-4">
                            <div className="flex gap-6 min-w-max">
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
                        </div>
                    </div>

                    {/* Calendar Widget */}
                    <WeeklyCalendar
                        slots={slots}
                        onAddSlot={handleAddSlot}
                        onDeleteSlot={handleDeleteSlot}
                        compactMode={true}
                        onOpenFullCalendar={() => setActiveTab('calendar')}
                    />
                </div>
            )}

            {/* Lead Pipeline Tab */}
            {activeTab === 'leads' && (
                <div className="animate-fade-in">
                    <h1 className="text-3xl font-bold text-white mb-6">Lead Management</h1>
                    <LeadTable leads={leads} onExport={handleExportLeads} />
                </div>
            )}

            {/* Calendar Tab */}
            {activeTab === 'calendar' && (
                <div className="animate-fade-in">
                    <h1 className="text-3xl font-bold text-white mb-6">Availability Calendar</h1>
                    <WeeklyCalendar
                        slots={slots}
                        onAddSlot={handleAddSlot}
                        onDeleteSlot={handleDeleteSlot}
                    />
                </div>
            )}

            {/* Properties Tab */}
            {activeTab === 'properties' && (
                <div className="animate-fade-in">
                    <PropertiesManagement tenantId={tenantId} />
                </div>
            )}

            {/* Analytics Tab */}
            {activeTab === 'analytics' && (
                <div className="animate-fade-in">
                    <Analytics tenantId={tenantId} />
                </div>
            )}

            {/* QR Generator Tab */}
            {activeTab === 'qr' && (
                <div className="animate-fade-in">
                    <QRGenerator tenantId={tenantId} />
                </div>
            )}

            {/* Broadcast Tab */}
            {activeTab === 'broadcast' && (
                <div className="animate-fade-in">
                    <Broadcast tenantId={tenantId} />
                </div>
            )}

            {/* Catalogs Tab */}
            {activeTab === 'catalogs' && (
                <div className="animate-fade-in">
                    <Catalogs tenantId={tenantId} />
                </div>
            )}

            {/* Lottery Tab */}
            {activeTab === 'lottery' && (
                <div className="animate-fade-in">
                    <Lottery tenantId={tenantId} />
                </div>
            )}

            {/* Settings Tab */}
            {activeTab === 'settings' && (
                <div className="animate-fade-in">
                    <SettingsPage tenantId={tenantId} token={token} />
                </div>
            )}
        </Layout>
    );
};

export default Dashboard;
