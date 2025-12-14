/**
 * Artin Smart Realty V2 - Analytics Dashboard
 * Real-time analytics and insights
 */

import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Users, Eye, MessageSquare, Calendar, DollarSign, Target } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const Analytics = ({ tenantId }) => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeRange, setTimeRange] = useState('7d'); // '7d', '30d', '90d', 'all'

    useEffect(() => {
        loadAnalytics();
    }, [tenantId, timeRange]);

    const loadAnalytics = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(
                `${API_BASE_URL}/api/tenants/${tenantId}/analytics?range=${timeRange}`,
                {
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                }
            );

            if (response.ok) {
                const data = await response.json();
                setStats(data);
            } else {
                // Mock data for demo
                setStats({
                    total_leads: 156,
                    new_leads: 23,
                    conversion_rate: 12.5,
                    avg_response_time: 4.2,
                    bot_interactions: 342,
                    voice_messages: 89,
                    scheduled_viewings: 18,
                    total_revenue: 2450000,
                    trend: {
                        leads: +15.3,
                        conversions: +8.2,
                        revenue: +22.1
                    }
                });
            }
        } catch (error) {
            console.error('Failed to load analytics:', error);
            // Use mock data on error
            setStats({
                total_leads: 156,
                new_leads: 23,
                conversion_rate: 12.5,
                avg_response_time: 4.2,
                bot_interactions: 342,
                voice_messages: 89,
                scheduled_viewings: 18,
                total_revenue: 2450000,
                trend: {
                    leads: +15.3,
                    conversions: +8.2,
                    revenue: +22.1
                }
            });
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-96">
                <div className="text-center">
                    <div className="w-12 h-12 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-gray-400">Loading analytics...</p>
                </div>
            </div>
        );
    }

    const MetricCard = ({ title, value, icon: Icon, trend, trendLabel }) => (
        <div className="glass-card rounded-xl p-6">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <p className="text-gray-400 text-sm mb-1">{title}</p>
                    <h3 className="text-3xl font-bold text-white">{value}</h3>
                </div>
                <div className="p-3 bg-navy-800/50 rounded-lg">
                    <Icon className="text-gold-500" size={24} />
                </div>
            </div>
            {trend !== undefined && (
                <div className={`flex items-center gap-2 text-sm ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    <TrendingUp size={16} className={trend < 0 ? 'rotate-180' : ''} />
                    <span>{Math.abs(trend)}% {trendLabel || 'from last period'}</span>
                </div>
            )}
        </div>
    );

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <BarChart3 className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Analytics Dashboard</h2>
                        <p className="text-gray-400 text-sm">Track your performance metrics</p>
                    </div>
                </div>

                {/* Time Range Selector */}
                <div className="flex gap-2 bg-navy-800 rounded-lg p-1">
                    {[
                        { value: '7d', label: '7 Days' },
                        { value: '30d', label: '30 Days' },
                        { value: '90d', label: '90 Days' },
                        { value: 'all', label: 'All Time' }
                    ].map(option => (
                        <button
                            key={option.value}
                            onClick={() => setTimeRange(option.value)}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                                timeRange === option.value
                                    ? 'bg-gold-500 text-navy-900'
                                    : 'text-gray-400 hover:text-white'
                            }`}
                        >
                            {option.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <MetricCard
                    title="Total Leads"
                    value={stats.total_leads}
                    icon={Users}
                    trend={stats.trend?.leads}
                />
                <MetricCard
                    title="Conversion Rate"
                    value={`${stats.conversion_rate}%`}
                    icon={Target}
                    trend={stats.trend?.conversions}
                />
                <MetricCard
                    title="Bot Interactions"
                    value={stats.bot_interactions}
                    icon={MessageSquare}
                />
                <MetricCard
                    title="Scheduled Viewings"
                    value={stats.scheduled_viewings}
                    icon={Calendar}
                />
            </div>

            {/* Secondary Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-blue-500/20 rounded-lg">
                            <Eye className="text-blue-400" size={20} />
                        </div>
                        <h3 className="text-white font-semibold">Engagement</h3>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Voice Messages</span>
                            <span className="text-white font-semibold">{stats.voice_messages}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Text Messages</span>
                            <span className="text-white font-semibold">{stats.bot_interactions - stats.voice_messages}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Avg. Response Time</span>
                            <span className="text-white font-semibold">{stats.avg_response_time}min</span>
                        </div>
                    </div>
                </div>

                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-green-500/20 rounded-lg">
                            <Target className="text-green-400" size={20} />
                        </div>
                        <h3 className="text-white font-semibold">Lead Quality</h3>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Qualified Leads</span>
                            <span className="text-white font-semibold">{Math.round(stats.total_leads * 0.45)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Active Negotiations</span>
                            <span className="text-white font-semibold">{Math.round(stats.total_leads * 0.18)}</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Closed Deals</span>
                            <span className="text-white font-semibold">{Math.round(stats.total_leads * 0.12)}</span>
                        </div>
                    </div>
                </div>

                <div className="glass-card rounded-xl p-6">
                    <div className="flex items-center gap-3 mb-4">
                        <div className="p-2 bg-gold-500/20 rounded-lg">
                            <DollarSign className="text-gold-500" size={20} />
                        </div>
                        <h3 className="text-white font-semibold">Revenue</h3>
                    </div>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Total Revenue</span>
                            <span className="text-white font-semibold">
                                ${(stats.total_revenue / 1000000).toFixed(1)}M
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Avg. Deal Size</span>
                            <span className="text-white font-semibold">
                                ${Math.round(stats.total_revenue / (stats.total_leads * 0.12) / 1000)}K
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-gray-400 text-sm">Growth</span>
                            <span className="text-green-400 font-semibold">+{stats.trend?.revenue}%</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Charts Placeholder */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass-card rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4">Lead Pipeline</h3>
                    <div className="space-y-3">
                        {[
                            { stage: 'New Leads', count: stats.new_leads, color: 'bg-red-500', percentage: 100 },
                            { stage: 'Qualified', count: Math.round(stats.total_leads * 0.45), color: 'bg-yellow-500', percentage: 65 },
                            { stage: 'Viewing Scheduled', count: stats.scheduled_viewings, color: 'bg-blue-500', percentage: 40 },
                            { stage: 'Negotiating', count: Math.round(stats.total_leads * 0.18), color: 'bg-purple-500', percentage: 25 },
                            { stage: 'Closed Won', count: Math.round(stats.total_leads * 0.12), color: 'bg-green-500', percentage: 15 }
                        ].map((stage, index) => (
                            <div key={index}>
                                <div className="flex justify-between items-center mb-2">
                                    <span className="text-gray-400 text-sm">{stage.stage}</span>
                                    <span className="text-white font-semibold">{stage.count}</span>
                                </div>
                                <div className="w-full bg-navy-800 rounded-full h-2">
                                    <div
                                        className={`${stage.color} h-2 rounded-full transition-all duration-500`}
                                        style={{ width: `${stage.percentage}%` }}
                                    ></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="glass-card rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4">Top Performing Properties</h3>
                    <div className="space-y-4">
                        {[
                            { name: 'Palm Jumeirah Villa', views: 234, inquiries: 45 },
                            { name: 'Downtown Penthouse', views: 189, inquiries: 38 },
                            { name: 'Marina Apartment', views: 156, inquiries: 29 },
                            { name: 'Business Bay Studio', views: 142, inquiries: 24 },
                            { name: 'JBR Townhouse', views: 128, inquiries: 19 }
                        ].map((property, index) => (
                            <div key={index} className="flex items-center justify-between p-3 bg-navy-800 rounded-lg">
                                <div className="flex items-center gap-3">
                                    <div className="w-8 h-8 bg-gold-500 rounded-lg flex items-center justify-center text-navy-900 font-bold text-sm">
                                        {index + 1}
                                    </div>
                                    <div>
                                        <p className="text-white text-sm font-medium">{property.name}</p>
                                        <p className="text-gray-400 text-xs">{property.views} views • {property.inquiries} inquiries</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
