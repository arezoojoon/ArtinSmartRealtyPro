/**
 * Lead Generation Dashboard
 * AI-powered lead scraping and generation tools
 */

import React, { useState, useEffect } from 'react';
import {
    Target,
    Zap,
    Search,
    Download,
    Play,
    Pause,
    Settings,
    TrendingUp,
    Users,
    Building2,
    Globe,
    Plus,
    RefreshCw,
    CheckCircle,
    AlertCircle,
    Clock,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Stat Card Component
const StatCard = ({ title, value, icon: Icon, color = 'gold', subtitle }) => (
    <div className="glass-card p-5">
        <div className="flex items-center gap-4">
            <div className={`kpi-icon bg-${color}-500/20`}>
                <Icon className={`w-6 h-6 text-${color}-400`} />
            </div>
            <div>
                <p className="text-2xl font-bold text-white">{value}</p>
                <p className="text-sm text-gray-400">{title}</p>
                {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
            </div>
        </div>
    </div>
);

// Scraper Job Card
const ScraperJobCard = ({ job, onStart, onStop, onViewResults }) => {
    const getStatusBadge = (status) => {
        const badges = {
            running: { class: 'badge-green', label: 'Running', icon: Play },
            paused: { class: 'badge-yellow', label: 'Paused', icon: Pause },
            completed: { class: 'badge-blue', label: 'Completed', icon: CheckCircle },
            failed: { class: 'badge-red', label: 'Failed', icon: AlertCircle },
        };
        return badges[status] || badges.paused;
    };

    const badge = getStatusBadge(job.status);
    const StatusIcon = badge.icon;

    return (
        <div className="glass-card p-5">
            <div className="flex items-start justify-between mb-4">
                <div>
                    <h4 className="text-lg font-semibold text-white">{job.name}</h4>
                    <p className="text-sm text-gray-400 mt-1">{job.target}</p>
                </div>
                <span className={`badge ${badge.class} flex items-center gap-1.5`}>
                    <StatusIcon className="w-3 h-3" />
                    {badge.label}
                </span>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-navy-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400">Leads Found</p>
                    <p className="text-xl font-bold text-gold-400">{job.leads_found || 0}</p>
                </div>
                <div className="bg-navy-800/50 rounded-lg p-3">
                    <p className="text-xs text-gray-400">Last Run</p>
                    <p className="text-sm font-medium text-white">
                        {job.last_run ? new Date(job.last_run).toLocaleDateString() : 'Never'}
                    </p>
                </div>
            </div>

            <div className="flex gap-2">
                {job.status === 'running' ? (
                    <button
                        onClick={() => onStop(job.id)}
                        className="flex-1 btn-outline text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10 flex items-center justify-center gap-2"
                    >
                        <Pause className="w-4 h-4" />
                        Pause
                    </button>
                ) : (
                    <button
                        onClick={() => onStart(job.id)}
                        className="flex-1 btn-gold flex items-center justify-center gap-2"
                    >
                        <Play className="w-4 h-4" />
                        Start
                    </button>
                )}
                <button
                    onClick={() => onViewResults(job)}
                    className="btn-outline flex items-center justify-center gap-2 px-4"
                >
                    <Download className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
};

// Main Lead Generation Component
const LeadGeneration = ({ tenantId, token }) => {
    const [stats, setStats] = useState({
        totalLeadsGenerated: 0,
        activeJobs: 0,
        conversionRate: 0,
        sourcesConfigured: 0,
    });
    const [scraperJobs, setScraperJobs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateJob, setShowCreateJob] = useState(false);
    const [newJob, setNewJob] = useState({ name: '', target: '', source: 'google' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            // Fetch from API - fallback to sample data
            const response = await fetch(`${API_BASE_URL}/api/v1/lead-gen/stats`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setStats(data.stats || stats);
                setScraperJobs(data.jobs || []);
            }
        } catch (error) {
            console.error('Error fetching lead gen data:', error);
            // Sample data for demo
            setStats({
                totalLeadsGenerated: 3456,
                activeJobs: 2,
                conversionRate: 12.5,
                sourcesConfigured: 5,
            });
            setScraperJobs([
                {
                    id: 1,
                    name: 'Dubai Marina Dentists',
                    target: 'Dental clinics in Dubai Marina',
                    source: 'google_places',
                    status: 'running',
                    leads_found: 245,
                    last_run: new Date().toISOString(),
                },
                {
                    id: 2,
                    name: 'JBR Real Estate Investors',
                    target: 'Property investors in JBR area',
                    source: 'linkedin',
                    status: 'completed',
                    leads_found: 189,
                    last_run: new Date(Date.now() - 86400000).toISOString(),
                },
                {
                    id: 3,
                    name: 'Palm Jumeirah Homeowners',
                    target: 'Villa owners in Palm Jumeirah',
                    source: 'bayut_scraper',
                    status: 'paused',
                    leads_found: 67,
                    last_run: new Date(Date.now() - 172800000).toISOString(),
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleStartJob = async (jobId) => {
        try {
            await fetch(`${API_BASE_URL}/api/v1/lead-gen/jobs/${jobId}/start`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setScraperJobs(jobs => jobs.map(j =>
                j.id === jobId ? { ...j, status: 'running' } : j
            ));
        } catch (error) {
            console.error('Error starting job:', error);
            // Optimistic UI update
            setScraperJobs(jobs => jobs.map(j =>
                j.id === jobId ? { ...j, status: 'running' } : j
            ));
        }
    };

    const handleStopJob = async (jobId) => {
        try {
            await fetch(`${API_BASE_URL}/api/v1/lead-gen/jobs/${jobId}/stop`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${token}` }
            });
            setScraperJobs(jobs => jobs.map(j =>
                j.id === jobId ? { ...j, status: 'paused' } : j
            ));
        } catch (error) {
            console.error('Error stopping job:', error);
            setScraperJobs(jobs => jobs.map(j =>
                j.id === jobId ? { ...j, status: 'paused' } : j
            ));
        }
    };

    const handleViewResults = (job) => {
        alert(`Downloading ${job.leads_found} leads from "${job.name}"...`);
    };

    const handleCreateJob = async () => {
        if (!newJob.name || !newJob.target) return;

        const job = {
            id: Date.now(),
            ...newJob,
            status: 'paused',
            leads_found: 0,
            last_run: null,
        };
        setScraperJobs([...scraperJobs, job]);
        setShowCreateJob(false);
        setNewJob({ name: '', target: '', source: 'google' });
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="spinner" />
            </div>
        );
    }

    return (
        <div className="p-6 space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Target className="w-8 h-8 text-gold-400" />
                        Lead Generation
                    </h2>
                    <p className="text-gray-400 mt-1">AI-powered lead scraping and generation tools</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={fetchData}
                        className="btn-icon"
                        title="Refresh"
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>
                    <button
                        onClick={() => setShowCreateJob(true)}
                        className="btn-gold flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        New Scraper Job
                    </button>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                    title="Total Leads Generated"
                    value={stats.totalLeadsGenerated.toLocaleString()}
                    icon={Users}
                    color="gold"
                />
                <StatCard
                    title="Active Jobs"
                    value={stats.activeJobs}
                    icon={Zap}
                    color="green"
                />
                <StatCard
                    title="Conversion Rate"
                    value={`${stats.conversionRate}%`}
                    icon={TrendingUp}
                    color="blue"
                />
                <StatCard
                    title="Sources Configured"
                    value={stats.sourcesConfigured}
                    icon={Globe}
                    color="purple"
                />
            </div>

            {/* Active Sources */}
            <div className="glass-card p-5">
                <h3 className="text-lg font-semibold text-white mb-4">Active Lead Sources</h3>
                <div className="flex flex-wrap gap-3">
                    {['Google Places API', 'LinkedIn Sales Nav', 'Bayut Scraper', 'Property Finder', 'Facebook Ads'].map((source, i) => (
                        <div key={i} className="flex items-center gap-2 px-3 py-2 bg-navy-800/50 rounded-lg border border-white/5">
                            <span className={`w-2 h-2 rounded-full ${i < 3 ? 'bg-green-400' : 'bg-gray-400'}`} />
                            <span className="text-sm text-white">{source}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Scraper Jobs Grid */}
            <div>
                <h3 className="text-lg font-semibold text-white mb-4">Scraper Jobs</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {scraperJobs.map((job) => (
                        <ScraperJobCard
                            key={job.id}
                            job={job}
                            onStart={handleStartJob}
                            onStop={handleStopJob}
                            onViewResults={handleViewResults}
                        />
                    ))}
                </div>
            </div>

            {/* Create Job Modal */}
            {showCreateJob && (
                <div className="modal-overlay" onClick={() => setShowCreateJob(false)}>
                    <div className="modal-content" onClick={e => e.stopPropagation()}>
                        <h3 className="text-lg font-semibold text-white mb-4">Create New Scraper Job</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="input-label">Job Name</label>
                                <input
                                    type="text"
                                    value={newJob.name}
                                    onChange={(e) => setNewJob({ ...newJob, name: e.target.value })}
                                    className="input-field"
                                    placeholder="e.g., Dubai Marina Dentists"
                                />
                            </div>

                            <div>
                                <label className="input-label">Target Description</label>
                                <textarea
                                    value={newJob.target}
                                    onChange={(e) => setNewJob({ ...newJob, target: e.target.value })}
                                    className="input-field min-h-[80px]"
                                    placeholder="Describe what leads you want to find..."
                                />
                            </div>

                            <div>
                                <label className="input-label">Source</label>
                                <select
                                    value={newJob.source}
                                    onChange={(e) => setNewJob({ ...newJob, source: e.target.value })}
                                    className="select-field"
                                >
                                    <option value="google">Google Places API</option>
                                    <option value="linkedin">LinkedIn Sales Navigator</option>
                                    <option value="bayut">Bayut Scraper</option>
                                    <option value="propertyfinder">Property Finder</option>
                                </select>
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={() => setShowCreateJob(false)}
                                className="flex-1 btn-ghost"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateJob}
                                className="flex-1 btn-gold"
                            >
                                Create Job
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default LeadGeneration;
