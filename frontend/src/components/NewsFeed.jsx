/**
 * Artin Smart Realty - Market Insider News Feed
 * Real estate news, market updates, and insights
 */

import React, { useState, useEffect } from 'react';
import {
    Newspaper,
    TrendingUp,
    Calendar,
    User,
    ExternalLink,
    Heart,
    Share2,
    MessageCircle,
    Bookmark,
    RefreshCw,
    Filter,
    Search,
    Tag,
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Sample news data
const SAMPLE_NEWS = [
    {
        id: 1,
        title: 'Dubai Real Estate Market Sees 30% Growth in Q4 2024',
        summary: 'The Dubai property market continues its strong performance with transaction volumes reaching record highs...',
        content: 'The Dubai real estate market has shown remarkable resilience and growth...',
        category: 'market_update',
        source: 'Dubai Land Department',
        author: 'DLD Research Team',
        image: null,
        published_at: new Date(Date.now() - 3600000).toISOString(),
        likes: 245,
        comments: 32,
        featured: true,
    },
    {
        id: 2,
        title: 'New Luxury Developments Announced in Palm Jumeirah',
        summary: 'Three new ultra-luxury residential projects set to launch in early 2025...',
        content: 'Major developers have announced new projects...',
        category: 'development',
        source: 'Gulf Property',
        author: 'Sarah Johnson',
        image: null,
        published_at: new Date(Date.now() - 86400000).toISOString(),
        likes: 156,
        comments: 18,
        featured: false,
    },
    {
        id: 3,
        title: 'UAE Golden Visa Rules Updated for Property Investors',
        summary: 'New regulations make it easier for property investors to obtain long-term residency...',
        content: 'The UAE government has announced changes to the Golden Visa program...',
        category: 'regulation',
        source: 'UAE Government',
        author: 'GDRFA',
        image: null,
        published_at: new Date(Date.now() - 172800000).toISOString(),
        likes: 412,
        comments: 67,
        featured: true,
    },
    {
        id: 4,
        title: 'Interest Rates Impact on Dubai Mortgage Market',
        summary: 'Financial experts analyze the effects of changing interest rates on property purchases...',
        content: 'With global interest rate fluctuations...',
        category: 'finance',
        source: 'Emirates NBD',
        author: 'Banking Research',
        image: null,
        published_at: new Date(Date.now() - 259200000).toISOString(),
        likes: 89,
        comments: 14,
        featured: false,
    },
    {
        id: 5,
        title: 'Top 5 Emerging Areas for Property Investment in 2025',
        summary: 'Expert picks for the best ROI locations in Dubai real estate...',
        content: 'As Dubai continues to expand...',
        category: 'investment',
        source: 'Artin Realty',
        author: 'Investment Team',
        image: null,
        published_at: new Date(Date.now() - 345600000).toISOString(),
        likes: 328,
        comments: 45,
        featured: true,
    },
];

const CATEGORIES = [
    { id: 'all', label: 'All News', icon: Newspaper },
    { id: 'market_update', label: 'Market Updates', icon: TrendingUp },
    { id: 'development', label: 'New Developments', icon: Tag },
    { id: 'regulation', label: 'Regulations', icon: Tag },
    { id: 'finance', label: 'Finance', icon: Tag },
    { id: 'investment', label: 'Investment Tips', icon: Tag },
];

// News Card Component
const NewsCard = ({ article, onRead, onLike, featured = false }) => {
    const getCategoryBadge = (category) => {
        const badges = {
            market_update: 'badge-blue',
            development: 'badge-green',
            regulation: 'badge-yellow',
            finance: 'badge-purple',
            investment: 'badge-gold',
        };
        return badges[category] || 'badge-blue';
    };

    const formatDate = (date) => {
        const d = new Date(date);
        const now = new Date();
        const diff = Math.floor((now - d) / 1000 / 60); // minutes

        if (diff < 60) return `${diff}m ago`;
        if (diff < 1440) return `${Math.floor(diff / 60)}h ago`;
        return d.toLocaleDateString();
    };

    if (featured) {
        return (
            <div className="glass-card overflow-hidden group cursor-pointer" onClick={() => onRead(article)}>
                <div className="h-48 bg-gradient-to-br from-gold-500/20 to-navy-800 flex items-center justify-center">
                    <Newspaper className="w-16 h-16 text-gold-400/50" />
                    <span className="absolute top-4 left-4 badge badge-gold">⭐ Featured</span>
                </div>
                <div className="p-5">
                    <span className={`badge ${getCategoryBadge(article.category)} text-xs mb-3`}>
                        {article.category.replace('_', ' ')}
                    </span>
                    <h3 className="text-xl font-bold text-white mb-2 group-hover:text-gold-400 transition-colors">
                        {article.title}
                    </h3>
                    <p className="text-gray-400 text-sm line-clamp-2">{article.summary}</p>
                    <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/5">
                        <div className="flex items-center gap-2 text-sm text-gray-500">
                            <Calendar className="w-4 h-4" />
                            {formatDate(article.published_at)}
                        </div>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
                            <span className="flex items-center gap-1">
                                <Heart className="w-4 h-4" /> {article.likes}
                            </span>
                            <span className="flex items-center gap-1">
                                <MessageCircle className="w-4 h-4" /> {article.comments}
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div
            className="glass-card p-4 flex gap-4 group cursor-pointer hover:border-gold-500/30 transition-all"
            onClick={() => onRead(article)}
        >
            <div className="w-24 h-24 bg-navy-700 rounded-lg flex-shrink-0 flex items-center justify-center">
                <Newspaper className="w-8 h-8 text-gray-600" />
            </div>
            <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                    <div>
                        <span className={`badge ${getCategoryBadge(article.category)} text-xs mb-2`}>
                            {article.category.replace('_', ' ')}
                        </span>
                        <h4 className="text-white font-medium group-hover:text-gold-400 transition-colors line-clamp-2">
                            {article.title}
                        </h4>
                    </div>
                    <button
                        onClick={(e) => { e.stopPropagation(); onLike(article); }}
                        className="p-2 hover:bg-navy-700 rounded-lg text-gray-400 hover:text-red-400"
                    >
                        <Heart className="w-4 h-4" />
                    </button>
                </div>
                <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                    <span>{article.source}</span>
                    <span>•</span>
                    <span>{formatDate(article.published_at)}</span>
                </div>
            </div>
        </div>
    );
};

// Article Detail Modal
const ArticleModal = ({ article, onClose }) => {
    if (!article) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content max-w-2xl max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                <div className="h-48 bg-gradient-to-br from-gold-500/20 to-navy-800 rounded-xl mb-6 flex items-center justify-center">
                    <Newspaper className="w-16 h-16 text-gold-400/50" />
                </div>

                <h2 className="text-2xl font-bold text-white mb-4">{article.title}</h2>

                <div className="flex items-center gap-4 mb-6 text-sm text-gray-400">
                    <span className="flex items-center gap-1">
                        <User className="w-4 h-4" /> {article.author}
                    </span>
                    <span>•</span>
                    <span>{article.source}</span>
                    <span>•</span>
                    <span>{new Date(article.published_at).toLocaleDateString()}</span>
                </div>

                <p className="text-gray-300 leading-relaxed mb-6">{article.summary}</p>
                <p className="text-gray-300 leading-relaxed">{article.content}</p>

                <div className="flex items-center justify-between mt-6 pt-6 border-t border-white/10">
                    <div className="flex gap-4">
                        <button className="btn-outline flex items-center gap-2">
                            <Heart className="w-4 h-4" /> {article.likes}
                        </button>
                        <button className="btn-outline flex items-center gap-2">
                            <Share2 className="w-4 h-4" /> Share
                        </button>
                        <button className="btn-outline flex items-center gap-2">
                            <Bookmark className="w-4 h-4" /> Save
                        </button>
                    </div>
                    <button onClick={onClose} className="btn-gold">Close</button>
                </div>
            </div>
        </div>
    );
};

// Main News Feed Component
const NewsFeed = ({ tenantId, token }) => {
    const [news, setNews] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedArticle, setSelectedArticle] = useState(null);
    const [activeCategory, setActiveCategory] = useState('all');
    const [searchQuery, setSearchQuery] = useState('');

    useEffect(() => {
        fetchNews();
    }, []);

    const fetchNews = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/news`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                const articles = Array.isArray(data) ? data : (data.articles || []);
                setNews(articles.length > 0 ? articles : SAMPLE_NEWS);
            } else {
                // API error (4xx, 5xx) - use sample data
                console.error('News API returned error status:', response.status);
                setNews(SAMPLE_NEWS);
            }
        } catch (error) {
            console.error('Error fetching news:', error);
            setNews(SAMPLE_NEWS);
        } finally {
            setLoading(false);
        }
    };

    const filteredNews = news.filter(article => {
        if (activeCategory !== 'all' && article.category !== activeCategory) return false;
        if (searchQuery && !article.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
    });

    const featuredNews = filteredNews.filter(n => n.featured);
    const regularNews = filteredNews.filter(n => !n.featured);

    const handleLike = (article) => {
        setNews(news.map(n => n.id === article.id ? { ...n, likes: n.likes + 1 } : n));
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
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-3">
                        <Newspaper className="w-8 h-8 text-gold-400" />
                        Market Insider
                    </h2>
                    <p className="text-gray-400 mt-1">Real estate news, trends, and insights</p>
                </div>
                <button onClick={fetchNews} className="btn-outline flex items-center gap-2">
                    <RefreshCw className="w-4 h-4" />
                    Refresh
                </button>
            </div>

            {/* Search and Categories */}
            <div className="glass-card p-4">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                        <input
                            type="text"
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search news..."
                            className="input-field pl-10"
                        />
                    </div>
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                    {CATEGORIES.map(cat => (
                        <button
                            key={cat.id}
                            onClick={() => setActiveCategory(cat.id)}
                            className={`px-4 py-2 rounded-lg text-sm transition-all ${activeCategory === cat.id
                                ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                                : 'bg-navy-800 text-gray-400 hover:text-white'
                                }`}
                        >
                            {cat.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Featured News */}
            {featuredNews.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-white mb-4">Featured Stories</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {featuredNews.slice(0, 3).map(article => (
                            <NewsCard
                                key={article.id}
                                article={article}
                                featured
                                onRead={setSelectedArticle}
                                onLike={handleLike}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* Regular News */}
            <div>
                <h3 className="text-lg font-semibold text-white mb-4">Latest News</h3>
                <div className="space-y-4">
                    {regularNews.map(article => (
                        <NewsCard
                            key={article.id}
                            article={article}
                            onRead={setSelectedArticle}
                            onLike={handleLike}
                        />
                    ))}

                    {filteredNews.length === 0 && (
                        <div className="text-center py-12 text-gray-400">
                            No news found
                        </div>
                    )}
                </div>
            </div>

            {/* Article Modal */}
            {selectedArticle && (
                <ArticleModal
                    article={selectedArticle}
                    onClose={() => setSelectedArticle(null)}
                />
            )}
        </div>
    );
};

export default NewsFeed;
