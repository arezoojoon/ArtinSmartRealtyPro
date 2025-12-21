/**
 * Artin Smart Realty - Agent Dashboard (Sales Mode)
 * Restricted view for sales agents with assigned leads only
 */

import React, { useState, useEffect } from 'react';
import {
    Users,
    Clock,
    Phone,
    FileText,
    MessageSquare,
    Plus,
    CheckCircle,
    Calendar,
    MoreVertical,
    Send,
    ChevronRight,
    Bell,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// API Helper
const api = {
    async get(endpoint, token) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
        });
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },
    async post(endpoint, data, token) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(data),
        });
        if (!response.ok) throw new Error('API Error');
        return response.json();
    },
};

// Task Card Component
const TaskCard = ({ task, onComplete, onSnooze }) => {
    const getPriorityClass = (priority) => {
        switch (priority) {
            case 'high': return 'border-l-red-500 bg-red-500/5';
            case 'medium': return 'border-l-yellow-500 bg-yellow-500/5';
            default: return 'border-l-blue-500 bg-blue-500/5';
        }
    };

    return (
        <div className={`glass-card p-4 border-l-4 ${getPriorityClass(task.priority)}`}>
            <div className="flex items-start justify-between">
                <div className="flex-1">
                    <h4 className="font-medium text-white">{task.title}</h4>
                    <p className="text-sm text-gray-400 mt-1">{task.description}</p>
                    <div className="flex items-center gap-3 mt-3">
                        <span className="text-xs text-gold-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {task.dueTime}
                        </span>
                        {task.leadName && (
                            <span className="text-xs text-gray-500">
                                • {task.leadName}
                            </span>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => onComplete(task.id)}
                        className="p-2 rounded-lg hover:bg-green-500/20 text-gray-400 hover:text-green-400 transition-all"
                        title="Mark Complete"
                    >
                        <CheckCircle className="w-5 h-5" />
                    </button>
                    <button
                        onClick={() => onSnooze(task.id)}
                        className="p-2 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-white transition-all"
                        title="Snooze"
                    >
                        <Clock className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
};

// Lead Card Component for Agents
const AgentLeadCard = ({ lead, onAction }) => {
    const getHotnessClass = (score) => {
        if (score >= 80) return 'hotness-hot';
        if (score >= 50) return 'hotness-warm';
        return 'hotness-cold';
    };

    return (
        <div className="glass-card p-4 hover:border-gold-500/30 transition-all">
            <div className="flex items-start gap-3">
                <div className="lead-avatar flex-shrink-0">
                    {lead.name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-white truncate">{lead.name}</h4>
                        <span className={`hotness-badge ${getHotnessClass(lead.lead_score || 0)}`}>
                            {lead.lead_score || 0}°
                        </span>
                    </div>
                    <p className="text-sm text-gray-400 mt-1">
                        {lead.property_type} • {lead.preferred_location || 'Dubai'}
                    </p>
                    <p className="text-sm text-gold-400 mt-1">
                        ${lead.budget_min?.toLocaleString()} - ${lead.budget_max?.toLocaleString()}
                    </p>
                </div>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/5">
                <button
                    onClick={() => onAction('whatsapp', lead)}
                    className="flex-1 btn-outline text-sm py-2 flex items-center justify-center gap-2"
                >
                    <MessageSquare className="w-4 h-4" />
                    WhatsApp
                </button>
                <button
                    onClick={() => onAction('pdf', lead)}
                    className="flex-1 btn-outline text-sm py-2 flex items-center justify-center gap-2"
                >
                    <FileText className="w-4 h-4" />
                    Send PDF
                </button>
                <button
                    onClick={() => onAction('note', lead)}
                    className="p-2 btn-icon"
                >
                    <Plus className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
};

// Main Agent Dashboard Component
const AgentDashboard = ({ user, onLogout }) => {
    const [myLeads, setMyLeads] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('leads');
    const [showAddTask, setShowAddTask] = useState(false);
    const [newTask, setNewTask] = useState({ title: '', description: '', dueTime: '', leadId: null });

    const token = localStorage.getItem('token');

    // Fetch agent's assigned leads and tasks
    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);

                // Fetch assigned leads
                const leadsData = await api.get('/api/v1/agent/leads', token);
                setMyLeads(Array.isArray(leadsData) ? leadsData : (leadsData.leads || []));

                // Fetch tasks
                const tasksData = await api.get('/api/v1/agent/tasks', token);
                setTasks(Array.isArray(tasksData) ? tasksData : (tasksData.tasks || []));

            } catch (error) {
                console.error('Error fetching agent data:', error);
                // Sample data for demo
                setMyLeads([
                    { id: 1, name: 'Sarah Jenkins', property_type: 'Villa', preferred_location: 'Palm Jumeirah', budget_min: 2000000, budget_max: 5000000, lead_score: 85 },
                    { id: 2, name: 'Michael Chen', property_type: 'Penthouse', preferred_location: 'Downtown', budget_min: 3000000, budget_max: 3500000, lead_score: 72 },
                    { id: 3, name: 'Emma Davis', property_type: 'Apartment', preferred_location: 'Marina', budget_min: 1500000, budget_max: 2000000, lead_score: 65 },
                ]);

                setTasks([
                    { id: 1, title: 'Call Mr. Ahmadi', description: 'Follow up on Palm Villa viewing', dueTime: '4:00 PM Today', priority: 'high', leadName: 'Ahmad Ahmadi' },
                    { id: 2, title: 'Send Property Brochure', description: 'Email Marina Heights PDF', dueTime: '5:30 PM Today', priority: 'medium', leadName: 'Sarah Jenkins' },
                    { id: 3, title: 'Schedule Viewing', description: 'Book Downtown Penthouse tour', dueTime: 'Tomorrow 10:00 AM', priority: 'low', leadName: 'Michael Chen' },
                ]);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [token]);

    // Handle quick actions
    const handleAction = async (action, lead) => {
        switch (action) {
            case 'whatsapp':
                // Open WhatsApp with lead's phone
                if (lead.phone) {
                    window.open(`https://wa.me/${lead.phone}`, '_blank');
                } else {
                    alert('No phone number available for this lead');
                }
                break;
            case 'pdf':
                // Send property PDF
                try {
                    await api.post(`/api/v1/agent/leads/${lead.id}/pdf`, { type: 'property_brochure' }, token);
                    alert('PDF sent successfully!');
                } catch (error) {
                    console.error('Error sending PDF:', error);
                }
                break;
            case 'note':
                // Add note modal
                const note = prompt('Add a note for this lead:');
                if (note) {
                    try {
                        await api.post(`/api/v1/agent/leads/${lead.id}/note`, { content: note }, token);
                        alert('Note added!');
                    } catch (error) {
                        console.error('Error adding note:', error);
                    }
                }
                break;
        }
    };

    // Handle task completion
    const handleCompleteTask = async (taskId) => {
        try {
            await api.post(`/api/v1/agent/tasks/${taskId}/complete`, {}, token);
            setTasks(tasks.filter(t => t.id !== taskId));
        } catch (error) {
            console.error('Error completing task:', error);
            // Optimistically remove from UI for demo
            setTasks(tasks.filter(t => t.id !== taskId));
        }
    };

    // Handle task snooze
    const handleSnoozeTask = async (taskId) => {
        const snoozeTime = prompt('Snooze for how many hours?', '1');
        if (snoozeTime) {
            try {
                await api.post(`/api/v1/agent/tasks/${taskId}/snooze`, { hours: parseInt(snoozeTime) }, token);
                // Update UI
                setTasks(tasks.map(t =>
                    t.id === taskId ? { ...t, dueTime: `In ${snoozeTime}h` } : t
                ));
            } catch (error) {
                console.error('Error snoozing task:', error);
            }
        }
    };

    // Add new task
    const handleAddTask = async () => {
        if (!newTask.title) return;

        try {
            const created = await api.post('/api/v1/agent/tasks', newTask, token);
            setTasks([...tasks, created]);
            setShowAddTask(false);
            setNewTask({ title: '', description: '', dueTime: '', leadId: null });
        } catch (error) {
            console.error('Error creating task:', error);
            // Add locally for demo
            setTasks([...tasks, {
                id: Date.now(),
                ...newTask,
                priority: 'medium',
                dueTime: newTask.dueTime || 'Today'
            }]);
            setShowAddTask(false);
            setNewTask({ title: '', description: '', dueTime: '', leadId: null });
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 flex items-center justify-center">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-navy-950 via-navy-900 to-navy-800 p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white">My Dashboard</h1>
                    <p className="text-gray-400 mt-1">Welcome back, {user?.name || 'Agent'}</p>
                </div>
                <div className="flex items-center gap-4">
                    <button className="btn-icon notification-bell">
                        <Bell className="w-5 h-5" />
                        {tasks.length > 0 && (
                            <span className="notification-badge">{tasks.length}</span>
                        )}
                    </button>
                    <button onClick={onLogout} className="btn-outline">
                        Log Out
                    </button>
                </div>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
                <div className="glass-card p-5">
                    <div className="flex items-center gap-4">
                        <div className="kpi-icon">
                            <Users className="w-6 h-6 text-gold-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-white">{myLeads.length}</p>
                            <p className="text-sm text-gray-400">My Leads</p>
                        </div>
                    </div>
                </div>
                <div className="glass-card p-5">
                    <div className="flex items-center gap-4">
                        <div className="kpi-icon">
                            <Clock className="w-6 h-6 text-gold-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-white">{tasks.length}</p>
                            <p className="text-sm text-gray-400">Pending Tasks</p>
                        </div>
                    </div>
                </div>
                <div className="glass-card p-5">
                    <div className="flex items-center gap-4">
                        <div className="kpi-icon">
                            <CheckCircle className="w-6 h-6 text-gold-400" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-white">
                                {myLeads.filter(l => l.lead_score >= 70).length}
                            </p>
                            <p className="text-sm text-gray-400">Hot Leads</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex gap-4 mb-6 border-b border-white/10">
                <button
                    onClick={() => setActiveTab('leads')}
                    className={`pb-3 px-1 text-sm font-medium transition-colors ${activeTab === 'leads'
                            ? 'text-gold-400 border-b-2 border-gold-400'
                            : 'text-gray-400 hover:text-white'
                        }`}
                >
                    My Leads ({myLeads.length})
                </button>
                <button
                    onClick={() => setActiveTab('tasks')}
                    className={`pb-3 px-1 text-sm font-medium transition-colors ${activeTab === 'tasks'
                            ? 'text-gold-400 border-b-2 border-gold-400'
                            : 'text-gray-400 hover:text-white'
                        }`}
                >
                    Tasks & Reminders ({tasks.length})
                </button>
            </div>

            {/* Content */}
            {activeTab === 'leads' ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {myLeads.map((lead) => (
                        <AgentLeadCard
                            key={lead.id}
                            lead={lead}
                            onAction={handleAction}
                        />
                    ))}
                    {myLeads.length === 0 && (
                        <div className="col-span-full text-center py-12 text-gray-500">
                            No leads assigned to you yet
                        </div>
                    )}
                </div>
            ) : (
                <div className="space-y-4">
                    {/* Add Task Button */}
                    <button
                        onClick={() => setShowAddTask(true)}
                        className="w-full glass-card p-4 flex items-center justify-center gap-2 text-gold-400 hover:bg-navy-700/50 transition-all"
                    >
                        <Plus className="w-5 h-5" />
                        Add New Task
                    </button>

                    {/* Task List */}
                    {tasks.map((task) => (
                        <TaskCard
                            key={task.id}
                            task={task}
                            onComplete={handleCompleteTask}
                            onSnooze={handleSnoozeTask}
                        />
                    ))}

                    {tasks.length === 0 && (
                        <div className="text-center py-12 text-gray-500">
                            No pending tasks
                        </div>
                    )}
                </div>
            )}

            {/* Add Task Modal */}
            {showAddTask && (
                <div className="modal-overlay" onClick={() => setShowAddTask(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-white mb-4">Add New Task</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="input-label">Task Title</label>
                                <input
                                    type="text"
                                    value={newTask.title}
                                    onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                                    className="input-field"
                                    placeholder="e.g., Call client"
                                />
                            </div>

                            <div>
                                <label className="input-label">Description</label>
                                <textarea
                                    value={newTask.description}
                                    onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                                    className="input-field min-h-[80px]"
                                    placeholder="Task details..."
                                />
                            </div>

                            <div>
                                <label className="input-label">Due Time</label>
                                <input
                                    type="text"
                                    value={newTask.dueTime}
                                    onChange={(e) => setNewTask({ ...newTask, dueTime: e.target.value })}
                                    className="input-field"
                                    placeholder="e.g., 4:00 PM Today"
                                />
                            </div>

                            <div>
                                <label className="input-label">Related Lead</label>
                                <select
                                    value={newTask.leadId || ''}
                                    onChange={(e) => setNewTask({ ...newTask, leadId: e.target.value })}
                                    className="select-field"
                                >
                                    <option value="">Select a lead...</option>
                                    {myLeads.map((lead) => (
                                        <option key={lead.id} value={lead.id}>{lead.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setShowAddTask(false)}
                                className="flex-1 btn-ghost"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAddTask}
                                className="flex-1 btn-gold"
                            >
                                Add Task
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AgentDashboard;
