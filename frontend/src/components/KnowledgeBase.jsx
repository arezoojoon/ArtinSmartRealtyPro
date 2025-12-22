/**
 * Knowledge Base Management
 * Agent can add/edit/delete Dubai real estate information
 * Bot brain reads this data to answer customer questions
 */

import React, { useState, useEffect } from 'react';
import {
    BookOpen,
    Plus,
    Edit,
    Trash2,
    Save,
    X,
    Search,
    Filter,
    Tag,
    Globe,
    Star,
    CheckCircle,
    AlertCircle,
    ChevronDown,
    Brain,
    HelpCircle,
    FileText,
    MapPin,
    Building2
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Categories with icons and labels
const CATEGORIES = {
    faq: { icon: HelpCircle, label: 'FAQ' },
    policy: { icon: FileText, label: 'Laws & Policies' },
    location_info: { icon: MapPin, label: 'Location Info' },
    service: { icon: Building2, label: 'Services' },
    general: { icon: BookOpen, label: 'General' }
};

// Languages for bot responses (4 languages)
const LANGUAGES = {
    en: { label: 'English', flag: '🇬🇧' },
    fa: { label: 'Persian', flag: '🇮🇷' },
    ar: { label: 'Arabic', flag: '🇸🇦' },
    ru: { label: 'Russian', flag: '🇷🇺' }
};

const KnowledgeBase = ({ tenantId, token }) => {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [selectedLanguage, setSelectedLanguage] = useState('all');

    // Modal state
    const [showModal, setShowModal] = useState(false);
    const [editingEntry, setEditingEntry] = useState(null);
    const [formData, setFormData] = useState({
        category: 'general',
        title: '',
        content: '',
        language: 'en',
        keywords: '',
        priority: 0
    });
    const [saving, setSaving] = useState(false);

    // Fetch knowledge entries
    const fetchEntries = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/knowledge`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Failed to fetch knowledge entries');

            const data = await response.json();
            setEntries(data);
            setError(null);
        } catch (err) {
            console.error('Error fetching knowledge:', err);
            setError('Failed to load data');
            // Use sample data for demo
            setEntries([
                {
                    id: 1,
                    category: 'policy',
                    title: 'UAE Golden Visa Requirements',
                    content: 'With a property purchase of 2 million AED or more, you and your family can obtain a 10-year UAE residency. This visa does not require a sponsor and includes spouse and children.',
                    language: 'en',
                    keywords: ['golden visa', 'residency', 'UAE visa', '10 year visa'],
                    priority: 10,
                    is_active: true
                },
                {
                    id: 2,
                    category: 'faq',
                    title: 'ROI in Dubai Real Estate',
                    content: 'Rental yields in Dubai typically range from 7% to 10%, which is among the highest globally. Rental income is tax-free.',
                    language: 'en',
                    keywords: ['ROI', 'return on investment', 'rental yield', 'income'],
                    priority: 9,
                    is_active: true
                },
                {
                    id: 3,
                    category: 'location_info',
                    title: 'Dubai Marina Overview',
                    content: 'Dubai Marina is one of the most popular areas for investment. Excellent access to metro, beach, and shopping centers. Prices start from 800,000 AED.',
                    language: 'en',
                    keywords: ['Dubai Marina', 'marina', 'waterfront', 'investment'],
                    priority: 8,
                    is_active: true
                }
            ]);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (tenantId && token) {
            fetchEntries();
        }
    }, [tenantId, token]);

    // Filter entries
    const filteredEntries = entries.filter(entry => {
        const matchesSearch = searchQuery === '' ||
            entry.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            entry.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (entry.keywords && entry.keywords.some(k => k.toLowerCase().includes(searchQuery.toLowerCase())));

        const matchesCategory = selectedCategory === 'all' || entry.category === selectedCategory;
        const matchesLanguage = selectedLanguage === 'all' || entry.language === selectedLanguage;

        return matchesSearch && matchesCategory && matchesLanguage;
    });

    // Open modal for new entry
    const handleNewEntry = () => {
        setEditingEntry(null);
        setFormData({
            category: 'general',
            title: '',
            content: '',
            language: 'en',
            keywords: '',
            priority: 0
        });
        setShowModal(true);
    };

    // Open modal for editing
    const handleEdit = (entry) => {
        setEditingEntry(entry);
        setFormData({
            category: entry.category,
            title: entry.title,
            content: entry.content,
            language: entry.language,
            keywords: entry.keywords ? entry.keywords.join(', ') : '',
            priority: entry.priority || 0
        });
        setShowModal(true);
    };

    // Save entry
    const handleSave = async () => {
        try {
            setSaving(true);

            const payload = {
                ...formData,
                keywords: formData.keywords.split(',').map(k => k.trim()).filter(k => k),
                is_active: true
            };

            const url = editingEntry
                ? `${API_BASE_URL}/api/tenants/${tenantId}/knowledge/${editingEntry.id}`
                : `${API_BASE_URL}/api/tenants/${tenantId}/knowledge`;

            const method = editingEntry ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Failed to save');

            await fetchEntries();
            setShowModal(false);
        } catch (err) {
            console.error('Error saving:', err);
            alert('Failed to save entry');
        } finally {
            setSaving(false);
        }
    };

    // Delete entry
    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this entry?')) return;

        try {
            await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/knowledge/${id}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            await fetchEntries();
        } catch (err) {
            console.error('Error deleting:', err);
            alert('Failed to delete entry');
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center">
                            <Brain className="w-5 h-5 text-white" />
                        </div>
                        Bot Knowledge Base
                    </h1>
                    <p className="text-gray-400 mt-1">
                        Information added here is used by the bot to answer customer questions
                    </p>
                </div>

                <button
                    onClick={handleNewEntry}
                    className="btn-gradient flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium"
                >
                    <Plus className="w-5 h-5" />
                    Add New Entry
                </button>
            </div>

            {/* Filters */}
            <div className="glass-card rounded-2xl p-4">
                <div className="flex flex-col md:flex-row gap-4">
                    {/* Search */}
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search in title, content, or keywords..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white placeholder-gray-500 focus:border-gold-500/50 focus:outline-none"
                        />
                    </div>

                    {/* Category Filter */}
                    <div className="relative">
                        <select
                            value={selectedCategory}
                            onChange={(e) => setSelectedCategory(e.target.value)}
                            className="appearance-none bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 pr-10 text-white focus:border-gold-500/50 focus:outline-none cursor-pointer"
                        >
                            <option value="all">All Categories</option>
                            {Object.entries(CATEGORIES).map(([key, { label }]) => (
                                <option key={key} value={key}>{label}</option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>

                    {/* Language Filter */}
                    <div className="relative">
                        <select
                            value={selectedLanguage}
                            onChange={(e) => setSelectedLanguage(e.target.value)}
                            className="appearance-none bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 pr-10 text-white focus:border-gold-500/50 focus:outline-none cursor-pointer"
                        >
                            <option value="all">All Languages</option>
                            {Object.entries(LANGUAGES).map(([key, { label, flag }]) => (
                                <option key={key} value={key}>{flag} {label}</option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                    </div>
                </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="glass-card rounded-xl p-4 text-center">
                    <p className="text-3xl font-bold text-white">{entries.length}</p>
                    <p className="text-gray-400 text-sm">Total Entries</p>
                </div>
                <div className="glass-card rounded-xl p-4 text-center">
                    <p className="text-3xl font-bold text-green-400">{entries.filter(e => e.is_active).length}</p>
                    <p className="text-gray-400 text-sm">Active</p>
                </div>
                <div className="glass-card rounded-xl p-4 text-center">
                    <p className="text-3xl font-bold text-purple-400">{new Set(entries.map(e => e.category)).size}</p>
                    <p className="text-gray-400 text-sm">Categories</p>
                </div>
                <div className="glass-card rounded-xl p-4 text-center">
                    <p className="text-3xl font-bold text-gold-400">{new Set(entries.map(e => e.language)).size}</p>
                    <p className="text-gray-400 text-sm">Languages</p>
                </div>
            </div>

            {/* Entries List */}
            {loading ? (
                <div className="glass-card rounded-2xl p-12 text-center">
                    <div className="animate-spin w-12 h-12 border-4 border-gold-500 border-t-transparent rounded-full mx-auto"></div>
                    <p className="text-gray-400 mt-4">Loading...</p>
                </div>
            ) : filteredEntries.length === 0 ? (
                <div className="glass-card rounded-2xl p-12 text-center">
                    <BookOpen className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-white mb-2">No entries yet</h3>
                    <p className="text-gray-400 mb-6">
                        Add information about UAE laws, Golden Visa, ROI, etc. so the bot can answer customer questions
                    </p>
                    <button
                        onClick={handleNewEntry}
                        className="btn-gradient px-6 py-2.5 rounded-xl font-medium"
                    >
                        Add First Entry
                    </button>
                </div>
            ) : (
                <div className="space-y-4">
                    {filteredEntries.map((entry) => {
                        const CategoryIcon = CATEGORIES[entry.category]?.icon || BookOpen;
                        const langInfo = LANGUAGES[entry.language] || LANGUAGES.en;

                        return (
                            <div
                                key={entry.id}
                                className="glass-card glass-card-hover rounded-xl p-5 group"
                            >
                                <div className="flex items-start gap-4">
                                    {/* Icon */}
                                    <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 flex items-center justify-center flex-shrink-0">
                                        <CategoryIcon className="w-6 h-6 text-purple-400" />
                                    </div>

                                    {/* Content */}
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="text-lg font-semibold text-white truncate">
                                                {entry.title}
                                            </h3>
                                            <span className="text-sm">{langInfo.flag}</span>
                                            {entry.priority > 5 && (
                                                <Star className="w-4 h-4 text-gold-400 fill-gold-400" />
                                            )}
                                        </div>

                                        <p className="text-gray-400 text-sm line-clamp-2 mb-3">
                                            {entry.content}
                                        </p>

                                        {/* Tags */}
                                        <div className="flex flex-wrap gap-2">
                                            <span className="px-2 py-1 rounded-lg bg-purple-500/10 text-purple-400 text-xs border border-purple-500/20">
                                                {CATEGORIES[entry.category]?.label || entry.category}
                                            </span>
                                            {entry.keywords && entry.keywords.slice(0, 3).map((keyword, idx) => (
                                                <span
                                                    key={idx}
                                                    className="px-2 py-1 rounded-lg bg-navy-700/50 text-gray-400 text-xs border border-white/5"
                                                >
                                                    {keyword}
                                                </span>
                                            ))}
                                            {entry.keywords && entry.keywords.length > 3 && (
                                                <span className="px-2 py-1 rounded-lg bg-navy-700/50 text-gray-500 text-xs">
                                                    +{entry.keywords.length - 3}
                                                </span>
                                            )}
                                        </div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                        <button
                                            onClick={() => handleEdit(entry)}
                                            className="p-2 rounded-lg bg-blue-500/10 text-blue-400 hover:bg-blue-500/20 transition-colors"
                                        >
                                            <Edit className="w-4 h-4" />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(entry.id)}
                                            className="p-2 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 transition-colors"
                                        >
                                            <Trash2 className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
                    <div className="glass-card rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">
                                {editingEntry ? 'Edit Entry' : 'Add New Entry'}
                            </h2>
                            <button
                                onClick={() => setShowModal(false)}
                                className="p-2 rounded-lg hover:bg-white/10 transition-colors"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {/* Category & Language */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-2">
                                        Category
                                    </label>
                                    <select
                                        value={formData.category}
                                        onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                                        className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white focus:border-gold-500/50 focus:outline-none"
                                    >
                                        {Object.entries(CATEGORIES).map(([key, { label }]) => (
                                            <option key={key} value={key}>{label}</option>
                                        ))}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-2">
                                        Language (for bot response)
                                    </label>
                                    <select
                                        value={formData.language}
                                        onChange={(e) => setFormData({ ...formData, language: e.target.value })}
                                        className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white focus:border-gold-500/50 focus:outline-none"
                                    >
                                        {Object.entries(LANGUAGES).map(([key, { label, flag }]) => (
                                            <option key={key} value={key}>{flag} {label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* Title */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Title / Question
                                </label>
                                <input
                                    type="text"
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="e.g. What is UAE Golden Visa?"
                                    className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white placeholder-gray-500 focus:border-gold-500/50 focus:outline-none"
                                />
                            </div>

                            {/* Content */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Content / Answer
                                </label>
                                <textarea
                                    value={formData.content}
                                    onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                                    placeholder="Write the complete answer here. The bot will use this to respond to customers."
                                    rows={6}
                                    className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white placeholder-gray-500 focus:border-gold-500/50 focus:outline-none resize-none"
                                />
                            </div>

                            {/* Keywords */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Keywords (comma separated)
                                </label>
                                <input
                                    type="text"
                                    value={formData.keywords}
                                    onChange={(e) => setFormData({ ...formData, keywords: e.target.value })}
                                    placeholder="e.g. golden visa, residency, UAE visa, 10 year"
                                    className="w-full bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white placeholder-gray-500 focus:border-gold-500/50 focus:outline-none"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    The bot uses these keywords to find the right answer
                                </p>
                            </div>

                            {/* Priority */}
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-2">
                                    Priority (0-10)
                                </label>
                                <input
                                    type="number"
                                    min="0"
                                    max="10"
                                    value={formData.priority}
                                    onChange={(e) => setFormData({ ...formData, priority: parseInt(e.target.value) || 0 })}
                                    className="w-32 bg-navy-800/50 border border-white/10 rounded-xl py-2.5 px-4 text-white focus:border-gold-500/50 focus:outline-none"
                                />
                                <p className="text-xs text-gray-500 mt-1">
                                    Higher priority = shown first in results
                                </p>
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex justify-end gap-3 mt-6 pt-6 border-t border-white/10">
                            <button
                                onClick={() => setShowModal(false)}
                                className="px-4 py-2.5 rounded-xl border border-white/10 text-gray-400 hover:bg-white/5 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSave}
                                disabled={saving || !formData.title || !formData.content}
                                className="btn-gradient px-6 py-2.5 rounded-xl font-medium flex items-center gap-2 disabled:opacity-50"
                            >
                                {saving ? (
                                    <>
                                        <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
                                        Saving...
                                    </>
                                ) : (
                                    <>
                                        <Save className="w-4 h-4" />
                                        Save
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default KnowledgeBase;
