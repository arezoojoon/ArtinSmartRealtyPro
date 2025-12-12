/**
 * Lead Generation & Scraping Management Page
 * Configure LinkedIn scraping keywords, sources, and automation
 */

import React, { useState, useEffect } from 'react';
import {
    Search,
    Globe,
    Settings,
    Plus,
    Trash2,
    Play,
    Pause,
    TrendingUp,
    Users,
    Target,
    Eye,
    Edit,
    CheckCircle,
    XCircle
} from 'lucide-react';
import { Layout } from './Layout';

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
    
    async delete(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error(`API Error: ${response.statusText}`);
        return response.json();
    }
};

// ==================== COMPONENTS ====================

const StatCard = ({ title, value, icon: Icon, color = 'gold' }) => (
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
    </div>
);

const KeywordCard = ({ keyword, onDelete, onToggle }) => (
    <div className="glass-card rounded-xl p-4 flex items-center justify-between">
        <div className="flex items-center gap-3 flex-1">
            <div className={`w-3 h-3 rounded-full ${keyword.active ? 'bg-green-500' : 'bg-gray-500'}`}></div>
            <div className="flex-1">
                <h4 className="text-white font-medium text-sm">{keyword.keyword}</h4>
                <p className="text-gray-500 text-xs">
                    Sources: {keyword.sources.join(', ')} • Added {new Date(keyword.created_at).toLocaleDateString()}
                </p>
            </div>
            <div className="text-right">
                <div className="text-gold-500 font-bold text-sm">{keyword.leads_found || 0}</div>
                <div className="text-gray-500 text-xs">leads found</div>
            </div>
        </div>
        <div className="flex gap-2 ml-4">
            <button
                onClick={() => onToggle(keyword)}
                className={`p-2 rounded-lg transition-colors ${
                    keyword.active
                        ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        : 'bg-gray-500/20 text-gray-400 hover:bg-gray-500/30'
                }`}
            >
                {keyword.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </button>
            <button
                onClick={() => onDelete(keyword)}
                className="p-2 bg-red-500/20 text-red-400 hover:bg-red-500/30 rounded-lg transition-colors"
            >
                <Trash2 className="w-4 h-4" />
            </button>
        </div>
    </div>
);

// ==================== MAIN COMPONENT ====================

const LeadGeneration = () => {
    const [keywords, setKeywords] = useState([]);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [showAddForm, setShowAddForm] = useState(false);
    
    // Form state
    const [newKeyword, setNewKeyword] = useState('');
    const [selectedSources, setSelectedSources] = useState(['linkedin']);
    
    // Available sources
    const sources = [
        { id: 'linkedin', name: 'LinkedIn', icon: '💼' },
        { id: 'google', name: 'Google Search', icon: '🔍' },
        { id: 'twitter', name: 'Twitter/X', icon: '🐦' },
        { id: 'facebook', name: 'Facebook', icon: '👥' }
    ];
    
    useEffect(() => {
        fetchData();
    }, []);
    
    const fetchData = async () => {
        try {
            const [keywordsData, statsData] = await Promise.all([
                api.get('/api/linkedin/keywords'),
                api.get('/api/linkedin/stats')
            ]);
            
            setKeywords(keywordsData);
            setStats(statsData);
        } catch (error) {
            console.error('Failed to fetch lead generation data:', error);
            // Mock data for development
            setKeywords([
                {
                    id: 1,
                    keyword: 'real estate investor Dubai',
                    sources: ['linkedin'],
                    active: true,
                    leads_found: 45,
                    created_at: new Date().toISOString()
                },
                {
                    id: 2,
                    keyword: 'property buyer UAE',
                    sources: ['linkedin', 'google'],
                    active: true,
                    leads_found: 32,
                    created_at: new Date().toISOString()
                },
                {
                    id: 3,
                    keyword: 'expat looking for apartment Dubai',
                    sources: ['google'],
                    active: false,
                    leads_found: 18,
                    created_at: new Date().toISOString()
                }
            ]);
            setStats({
                total_keywords: 3,
                active_keywords: 2,
                total_leads_generated: 95,
                leads_this_month: 23
            });
        } finally {
            setLoading(false);
        }
    };
    
    const handleAddKeyword = async () => {
        if (!newKeyword.trim()) {
            alert('Please enter a keyword');
            return;
        }
        
        if (selectedSources.length === 0) {
            alert('Please select at least one source');
            return;
        }
        
        try {
            await api.post('/api/linkedin/keywords', {
                keyword: newKeyword,
                sources: selectedSources,
                active: true
            });
            
            setNewKeyword('');
            setSelectedSources(['linkedin']);
            setShowAddForm(false);
            fetchData();
            alert('✅ Keyword added successfully!');
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    };
    
    const handleDeleteKeyword = async (keyword) => {
        if (!confirm(`Delete keyword "${keyword.keyword}"?`)) return;
        
        try {
            await api.delete(`/api/linkedin/keywords/${keyword.id}`);
            fetchData();
            alert('✅ Keyword deleted successfully!');
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    };
    
    const handleToggleKeyword = async (keyword) => {
        try {
            await api.post(`/api/linkedin/keywords/${keyword.id}/toggle`, {
                active: !keyword.active
            });
            fetchData();
        } catch (error) {
            alert(`❌ Error: ${error.message}`);
        }
    };
    
    const toggleSource = (sourceId) => {
        setSelectedSources(prev =>
            prev.includes(sourceId)
                ? prev.filter(s => s !== sourceId)
                : [...prev, sourceId]
        );
    };
    
    if (loading) {
        return (
            <Layout>
                <div className="flex items-center justify-center h-96">
                    <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
                </div>
            </Layout>
        );
    }
    
    return (
        <Layout>
            <div className="space-y-6 animate-fade-in">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                            <Target className="w-8 h-8 text-gold-500" />
                            Lead Generation
                        </h1>
                        <p className="text-gray-400">
                            Configure keywords and sources for automated lead scraping
                        </p>
                    </div>
                    <button
                        onClick={() => setShowAddForm(!showAddForm)}
                        className="px-6 py-3 btn-gold rounded-xl flex items-center gap-2"
                    >
                        <Plus className="w-5 h-5" />
                        Add Keyword
                    </button>
                </div>
                
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <StatCard
                        title="Total Keywords"
                        value={stats?.total_keywords || 0}
                        icon={Search}
                        color="blue"
                    />
                    <StatCard
                        title="Active Keywords"
                        value={stats?.active_keywords || 0}
                        icon={CheckCircle}
                        color="green"
                    />
                    <StatCard
                        title="Total Leads"
                        value={stats?.total_leads_generated || 0}
                        icon={Users}
                        color="gold"
                    />
                    <StatCard
                        title="This Month"
                        value={stats?.leads_this_month || 0}
                        icon={TrendingUp}
                        color="purple"
                    />
                </div>
                
                {/* Add Keyword Form */}
                {showAddForm && (
                    <div className="glass-card rounded-2xl p-6 border-2 border-gold-500/30">
                        <h3 className="text-xl font-bold text-white mb-4">Add New Keyword</h3>
                        
                        <div className="space-y-4">
                            {/* Keyword Input */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Keyword / Search Query
                                </label>
                                <input
                                    type="text"
                                    value={newKeyword}
                                    onChange={(e) => setNewKeyword(e.target.value)}
                                    placeholder="e.g., real estate investor Dubai"
                                    className="w-full px-4 py-3 bg-navy-800/50 border border-white/10 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-gold-500/50 transition-colors"
                                />
                                <p className="text-xs text-gray-500 mt-2">
                                    💡 Tip: Use specific keywords like "property buyer UAE" or "luxury apartment investor"
                                </p>
                            </div>
                            
                            {/* Sources Selection */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Search Sources (Select one or more)
                                </label>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                                    {sources.map(source => (
                                        <button
                                            key={source.id}
                                            onClick={() => toggleSource(source.id)}
                                            className={`p-4 rounded-xl border-2 transition-all ${
                                                selectedSources.includes(source.id)
                                                    ? 'border-gold-500 bg-gold-500/20'
                                                    : 'border-white/10 bg-white/5 hover:border-white/20'
                                            }`}
                                        >
                                            <div className="text-2xl mb-2">{source.icon}</div>
                                            <div className={`text-sm font-medium ${
                                                selectedSources.includes(source.id) ? 'text-gold-400' : 'text-gray-400'
                                            }`}>
                                                {source.name}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                            
                            {/* Action Buttons */}
                            <div className="flex gap-3 pt-4">
                                <button
                                    onClick={handleAddKeyword}
                                    className="flex-1 px-6 py-3 btn-gold rounded-xl flex items-center justify-center gap-2"
                                >
                                    <Plus className="w-5 h-5" />
                                    Add Keyword
                                </button>
                                <button
                                    onClick={() => setShowAddForm(false)}
                                    className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl transition-colors"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                )}
                
                {/* Keywords List */}
                <div className="space-y-3">
                    <h3 className="text-xl font-bold text-white">Active Keywords</h3>
                    {keywords.length > 0 ? (
                        keywords.map(keyword => (
                            <KeywordCard
                                key={keyword.id}
                                keyword={keyword}
                                onDelete={handleDeleteKeyword}
                                onToggle={handleToggleKeyword}
                            />
                        ))
                    ) : (
                        <div className="glass-card rounded-xl p-12 text-center">
                            <Search className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                            <h3 className="text-xl font-bold text-white mb-2">No Keywords Yet</h3>
                            <p className="text-gray-400 mb-6">
                                Add your first keyword to start generating leads automatically
                            </p>
                            <button
                                onClick={() => setShowAddForm(true)}
                                className="px-6 py-3 btn-gold rounded-xl inline-flex items-center gap-2"
                            >
                                <Plus className="w-5 h-5" />
                                Add Your First Keyword
                            </button>
                        </div>
                    )}
                </div>
                
                {/* Info Section */}
                <div className="glass-card rounded-2xl p-6 border-l-4 border-blue-500">
                    <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                        <Globe className="w-5 h-5 text-blue-500" />
                        How Lead Generation Works
                    </h3>
                    <div className="space-y-2 text-sm text-gray-300">
                        <p>🔍 <strong>LinkedIn:</strong> Scrapes public profiles matching your keywords (requires Chrome Extension)</p>
                        <p>🌐 <strong>Google:</strong> Searches for businesses and contact information</p>
                        <p>🐦 <strong>Twitter/X:</strong> Finds potential leads from tweets and profiles</p>
                        <p>👥 <strong>Facebook:</strong> Searches groups and pages for interested buyers</p>
                        <p className="pt-2 text-gold-400">
                            💡 All leads are automatically added to your CRM with follow-up campaigns enabled
                        </p>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default LeadGeneration;
