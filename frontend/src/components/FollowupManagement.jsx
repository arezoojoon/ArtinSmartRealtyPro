/**
 * Follow-up Management Page
 * Manage automated follow-up campaigns and schedules
 */

import React, { useState, useEffect } from 'react';
import {
    Clock,
    Send,
    Users,
    TrendingUp,
    Calendar,
    Play,
    Pause,
    Edit,
    Eye,
    CheckCircle,
    XCircle,
    AlertCircle,
    RefreshCw,
    MessageSquare
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const api = {
    async get(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: getAuthHeaders(),
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
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
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    },

    async patch(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }
};

// ==================== COMPONENTS ====================

// Stats Card
const StatCard = ({ title, value, icon: Icon, color = 'gold', trend }) => (
    <div className="glass-card glass-card-hover rounded-2xl p-6">
        <div className="flex items-start justify-between mb-4">
            <p className="text-sm font-medium text-white/50 uppercase tracking-wider">
                {title}
            </p>
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center bg-${color}-500/20`}>
                <Icon className={`w-6 h-6 text-${color}-500`} />
            </div>
        </div>
        <h3 className="text-3xl font-bold text-white">{value}</h3>
        {trend && (
            <p className="text-sm text-green-400 mt-2">{trend}</p>
        )}
    </div>
);

// Temperature Badge
const TemperatureBadge = ({ temp }) => {
    const badges = {
        burning: { emoji: '🔥', color: 'bg-red-500/20 text-red-400 border-red-500/30', label: 'BURNING' },
        hot: { emoji: '🌶️', color: 'bg-orange-500/20 text-orange-400 border-orange-500/30', label: 'HOT' },
        warm: { emoji: '☀️', color: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30', label: 'WARM' },
        cold: { emoji: '❄️', color: 'bg-blue-500/20 text-blue-400 border-blue-500/30', label: 'COLD' },
    };
    const badge = badges[temp] || badges.cold;

    return (
        <div className={`flex items-center gap-1 px-2 py-1 rounded-lg border text-xs font-bold ${badge.color}`}>
            <span>{badge.emoji}</span>
            <span>{badge.label}</span>
        </div>
    );
};

// Follow-up Lead Card
const FollowupLeadCard = ({ lead, onSendManual, onUpdateSchedule, onViewDetails }) => {
    const getStatusColor = (status) => {
        const colors = {
            new: 'bg-red-500/15 text-red-400 border-red-500/30',
            contacted: 'bg-orange-500/15 text-orange-400 border-orange-500/30',
            qualified: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/30',
            nurturing: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
        };
        return colors[status] || 'bg-gray-500/15 text-gray-400 border-gray-500/30';
    };

    const getStageLabel = (count) => {
        const stages = ['Introduction', 'Value Prop', 'Urgency', 'Last Chance', 'Exit'];
        return stages[count] || `Stage ${count}`;
    };

    const isOverdue = lead.next_followup_at && new Date(lead.next_followup_at) <= new Date();

    return (
        <div className="glass-card glass-card-hover rounded-xl p-4">
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3 flex-1">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center text-navy-900 font-bold">
                        {lead.full_name ? lead.full_name.charAt(0).toUpperCase() : '?'}
                    </div>
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-white font-medium text-sm truncate">
                                {lead.full_name || 'Anonymous'}
                            </h4>
                            {lead.lead_score > 0 && (
                                <span className="text-xs font-bold text-gold-500 bg-gold-500/10 px-2 py-0.5 rounded flex-shrink-0">
                                    {lead.lead_score}
                                </span>
                            )}
                            <span className={`text-xs px-2 py-0.5 rounded border font-medium ${getStatusColor(lead.status)}`}>
                                {lead.status.toUpperCase()}
                            </span>
                        </div>
                        <p className="text-gray-500 text-xs">
                            {lead.phone || lead.email || 'No contact info'}
                        </p>
                    </div>
                </div>
                {lead.temperature && <TemperatureBadge temp={lead.temperature} />}
            </div>

            {/* Follow-up Info */}
            <div className="space-y-2 mb-3 p-3 bg-white/5 rounded-xl border border-white/10">
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">Next Follow-up:</span>
                    <span className={`font-medium ${isOverdue ? 'text-red-400' : 'text-white'}`}>
                        {lead.next_followup_at
                            ? new Date(lead.next_followup_at).toLocaleString()
                            : 'Not scheduled'
                        }
                        {isOverdue && <span className="ml-1">⏰ OVERDUE</span>}
                    </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">Stage:</span>
                    <span className="text-white font-medium">
                        {getStageLabel(lead.followup_count)} ({lead.followup_count}/5)
                    </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">Last Contact:</span>
                    <span className="text-white font-medium">
                        {lead.last_contacted_at
                            ? new Date(lead.last_contacted_at).toLocaleDateString()
                            : 'Never'
                        }
                    </span>
                </div>
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-400">Source:</span>
                    <span className="text-white font-medium">{lead.source.toUpperCase()}</span>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
                <button
                    onClick={() => onSendManual(lead)}
                    className="flex-1 px-3 py-2 btn-gold rounded-lg flex items-center justify-center gap-2 text-xs"
                >
                    <Send className="w-3 h-3" />
                    Send Now
                </button>
                <button
                    onClick={() => onUpdateSchedule(lead)}
                    className="flex-1 px-3 py-2 bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 rounded-lg flex items-center justify-center gap-2 text-xs transition-colors"
                >
                    <Calendar className="w-3 h-3" />
                    Reschedule
                </button>
                <button
                    onClick={() => onViewDetails(lead)}
                    className="px-3 py-2 bg-white/10 text-white hover:bg-white/20 rounded-lg flex items-center justify-center transition-colors"
                >
                    <Eye className="w-3 h-3" />
                </button>
            </div>
        </div>
    );
};

// Template Card
const TemplateCard = ({ template }) => (
    <div className="glass-card rounded-xl p-4">
        <div className="flex items-start justify-between mb-3">
            <div>
                <h4 className="text-white font-medium text-sm mb-1">
                    Stage {template.stage}: {template.template_name}
                </h4>
                <span className="text-xs text-gray-500">Used in automated follow-ups</span>
            </div>
            <button className="p-2 hover:bg-white/10 rounded-lg transition-colors">
                <Edit className="w-4 h-4 text-gray-400" />
            </button>
        </div>
        <div className="p-3 bg-navy-800/50 rounded-lg border border-white/5">
            <p className="text-sm text-gray-300 italic">{template.template_preview}</p>
        </div>
    </div>
);

// ==================== MAIN COMPONENT ====================

const FollowupManagement = () => {
    const [stats, setStats] = useState(null);
    const [leads, setLeads] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [sendingLeadId, setSendingLeadId] = useState(null);
    const [pendingOnly, setPendingOnly] = useState(true);

    useEffect(() => {
        fetchData();
    }, [pendingOnly]);

    const fetchData = async () => {
        try {
            const [statsData, leadsData, templatesData] = await Promise.all([
                api.get('/api/followup/stats'),
                api.get(`/api/followup/leads?pending_only=${pendingOnly}`),
                api.get('/api/followup/templates')
            ]);

            setStats(statsData);
            setLeads(leadsData);
            setTemplates(templatesData);
        } catch (error) {
            console.error('Failed to fetch follow-up data:', error);
            // Sample data fallback
            setStats({
                total_scheduled: 45,
                pending: 8,
                sent_today: 12,
                success_rate: 78,
                by_stage: { 0: 15, 1: 12, 2: 8, 3: 6, 4: 4 }
            });
            setLeads([
                { id: 1, full_name: 'Sarah Jenkins', phone: '+971501234567', email: 'sarah@email.com', status: 'new', temperature: 'hot', lead_score: 85, source: 'whatsapp', followup_count: 1, next_followup_at: new Date(Date.now() + 3600000).toISOString(), last_contacted_at: new Date(Date.now() - 86400000).toISOString() },
                { id: 2, full_name: 'Michael Chen', phone: '+971507654321', email: 'michael@email.com', status: 'qualified', temperature: 'warm', lead_score: 72, source: 'telegram', followup_count: 2, next_followup_at: new Date(Date.now() - 1800000).toISOString(), last_contacted_at: new Date(Date.now() - 172800000).toISOString() },
                { id: 3, full_name: 'Emma Davis', phone: '+971509876543', email: 'emma@email.com', status: 'contacted', temperature: 'burning', lead_score: 92, source: 'whatsapp', followup_count: 0, next_followup_at: new Date(Date.now() + 7200000).toISOString(), last_contacted_at: null },
            ]);
            setTemplates([
                { stage: 0, template_name: 'Introduction', template_preview: 'Hi {name}! 👋 Thanks for your interest in {property_type}. I\'m here to help you find your dream property in Dubai...' },
                { stage: 1, template_name: 'Value Proposition', template_preview: 'Hi {name}! 🏡 Just wanted to share some amazing properties that match your criteria. We have exclusive listings in {location}...' },
                { stage: 2, template_name: 'Create Urgency', template_preview: '{name}, I noticed the property you liked is getting a lot of interest! Would you like to schedule a viewing before it\'s gone? 🔥' },
                { stage: 3, template_name: 'Last Chance', template_preview: 'Hi {name}! This is your last chance to see the {property_type} in {location}. The owner is finalizing offers this week. Should I reserve a slot? ⏰' },
                { stage: 4, template_name: 'Exit Message', template_preview: '{name}, I understand if now isn\'t the right time. Feel free to reach out whenever you\'re ready. Wishing you all the best! 🙏' },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleSendManual = async (lead) => {
        if (!confirm(`Send follow-up message to ${lead.full_name}?`)) return;

        setSendingLeadId(lead.id);
        try {
            const result = await api.post('/api/followup/manual', {
                lead_id: lead.id
            });

            if (result.success) {
                alert(`✅ Follow-up sent successfully via ${result.channel}!`);
                fetchData(); // Refresh data
            } else {
                alert(`❌ Failed to send follow-up: ${result.message}`);
            }
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        } finally {
            setSendingLeadId(null);
        }
    };

    const handleUpdateSchedule = async (lead) => {
        const hours = prompt(`Reschedule follow-up for ${lead.full_name}.\nEnter hours from now (or 0 to disable):`, '24');
        if (hours === null) return;

        try {
            const hoursNum = parseInt(hours);
            const nextFollowupAt = hoursNum > 0
                ? new Date(Date.now() + hoursNum * 60 * 60 * 1000).toISOString()
                : null;

            await api.patch('/api/followup/schedule', {
                lead_id: lead.id,
                next_followup_at: nextFollowupAt,
                followup_enabled: hoursNum > 0
            });

            alert('✅ Follow-up schedule updated!');
            fetchData();
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    };

    const handleViewDetails = (lead) => {
        alert(`Lead Details:\n\nName: ${lead.full_name}\nEmail: ${lead.email || 'N/A'}\nPhone: ${lead.phone || 'N/A'}\nScore: ${lead.lead_score}\nStatus: ${lead.status}`);
    };

    const handleTestEngine = async () => {
        if (!confirm('Run follow-up engine now? This will send pending follow-ups.')) return;

        try {
            const result = await api.post('/api/followup/test-engine', {});
            alert(`✅ Follow-up engine executed!\n\nResults: ${JSON.stringify(result.results, null, 2)}`);
            fetchData();
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    };

    if (loading) {
        return (
            <div className="p-6">
                <div className="flex items-center justify-center h-96">
                    <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                        <MessageSquare className="w-8 h-8 text-gold-500" />
                        Follow-up Management
                    </h1>
                    <p className="text-gray-400">
                        Automated lead nurturing across Telegram & WhatsApp
                    </p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => fetchData()}
                        className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white rounded-xl flex items-center gap-2 transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                    <button
                        onClick={handleTestEngine}
                        className="px-4 py-2 btn-gold rounded-xl flex items-center gap-2"
                    >
                        <Play className="w-4 h-4" />
                        Run Engine Now
                    </button>
                </div>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <StatCard
                    title="Total Scheduled"
                    value={stats?.total_scheduled || 0}
                    icon={Users}
                    color="blue"
                />
                <StatCard
                    title="Pending Now"
                    value={stats?.pending || 0}
                    icon={AlertCircle}
                    color="orange"
                    trend={stats?.pending > 0 ? '⏰ Needs attention' : '✅ All caught up'}
                />
                <StatCard
                    title="Sent Today"
                    value={stats?.sent_today || 0}
                    icon={Send}
                    color="green"
                />
                <StatCard
                    title="Success Rate"
                    value={`${stats?.success_rate || 0}%`}
                    icon={TrendingUp}
                    color="gold"
                />
            </div>

            {/* Stage Distribution */}
            {stats?.by_stage && Object.keys(stats.by_stage).length > 0 && (
                <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-xl font-bold text-white mb-4">Follow-up Stages</h3>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                        {Object.entries(stats.by_stage).map(([stage, count]) => {
                            const stages = ['Introduction', 'Value Prop', 'Urgency', 'Last Chance', 'Exit'];
                            return (
                                <div key={stage} className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
                                    <div className="text-2xl font-bold text-gold-500">{count}</div>
                                    <div className="text-xs text-gray-400 mt-1">{stages[stage] || `Stage ${stage}`}</div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Filter */}
            <div className="flex items-center gap-3">
                <button
                    onClick={() => setPendingOnly(!pendingOnly)}
                    className={`px-4 py-2 rounded-xl flex items-center gap-2 transition-colors ${pendingOnly
                        ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                        : 'bg-white/10 text-white hover:bg-white/20'
                        }`}
                >
                    <Clock className="w-4 h-4" />
                    {pendingOnly ? 'Pending Only' : 'All Scheduled'}
                </button>
                <span className="text-sm text-gray-400">
                    {leads.length} lead(s) shown
                </span>
            </div>

            {/* Leads Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {leads.length > 0 ? (
                    leads.map(lead => (
                        <FollowupLeadCard
                            key={lead.id}
                            lead={lead}
                            onSendManual={handleSendManual}
                            onUpdateSchedule={handleUpdateSchedule}
                            onViewDetails={handleViewDetails}
                        />
                    ))
                ) : (
                    <div className="col-span-2 text-center py-12 text-gray-400">
                        {pendingOnly
                            ? '✅ No pending follow-ups! All caught up.'
                            : 'No leads with follow-up scheduled.'
                        }
                    </div>
                )}
            </div>

            {/* Templates Section */}
            <div className="space-y-4">
                <h3 className="text-xl font-bold text-white">Follow-up Message Templates</h3>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {templates.map(template => (
                        <TemplateCard key={template.stage} template={template} />
                    ))}
                </div>
            </div>
        </div>
    );
};

export default FollowupManagement;
