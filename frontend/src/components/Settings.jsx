/**
 * Artin Smart Realty V2 - Settings Page
 * Agent settings for Telegram/WhatsApp bot configuration
 */

import React, { useState, useEffect } from 'react';
import {
    Settings as SettingsIcon,
    Save,
    Copy,
    Check,
    Bot,
    MessageCircle,
    Palette,
    Building2,
    Phone,
    Mail,
    Globe,
    ExternalLink,
    Eye,
    EyeOff,
    Clock,
    Plus,
    Trash2
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const Settings = ({ tenantId, token }) => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [copied, setCopied] = useState(null);
    const [showWhatsAppToken, setShowWhatsAppToken] = useState(false);
    const [showTelegramToken, setShowTelegramToken] = useState(false);
    const [currentWhatsAppToken, setCurrentWhatsAppToken] = useState('');
    const [currentTelegramToken, setCurrentTelegramToken] = useState('');
    const [activeTab, setActiveTab] = useState('profile'); // profile, bots, schedule
    const [schedule, setSchedule] = useState([]);
    const [loadingSchedule, setLoadingSchedule] = useState(false);
    
    // Settings state
    const [settings, setSettings] = useState({
        name: '',
        company_name: '',
        phone: '',
        email: '',
        logo_url: '',
        primary_color: '#D4AF37',
        telegram_bot_token: '',
        whatsapp_phone_number_id: '',
        whatsapp_access_token: '',
        whatsapp_business_account_id: '',
        whatsapp_verify_token: '',
    });

    useEffect(() => {
        fetchSettings();
        // Don't auto-load schedule to prevent duplicate accumulation
        // User must explicitly click "Load Current Schedule" or start fresh
    }, [tenantId]);

    const fetchSettings = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (!response.ok) throw new Error('Failed to fetch settings');
            
            const data = await response.json();
            setSettings({
                name: data.name || '',
                company_name: data.company_name || '',
                phone: data.phone || '',
                email: data.email || '',
                logo_url: data.logo_url || '',
                primary_color: data.primary_color || '#D4AF37',
                telegram_bot_token: data.telegram_bot_token || '',
                whatsapp_phone_number_id: data.whatsapp_phone_number_id || '',
                whatsapp_access_token: '', // Don't show existing token for security
                whatsapp_business_account_id: data.whatsapp_business_account_id || '',
                whatsapp_verify_token: data.whatsapp_verify_token || '',
            });
            
            // Store current tokens for display
            setCurrentTelegramToken(data.telegram_bot_token || '');
            setCurrentWhatsAppToken(data.whatsapp_access_token || '');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        try {
            setSaving(true);
            setError(null);
            setSuccess(null);
            
            // Build update object - only include non-empty fields
            const updateData = {};
            Object.keys(settings).forEach(key => {
                if (settings[key] && settings[key].trim) {
                    const value = settings[key].trim();
                    if (value) updateData[key] = value;
                } else if (settings[key]) {
                    updateData[key] = settings[key];
                }
            });
            
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify(updateData),
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Failed to save settings');
            }
            
            setSuccess('Settings saved successfully!');
        } catch (err) {
            setError(err.message);
        } finally {
            setSaving(false);
        }
    };

    const fetchSchedule = async () => {
        try {
            setLoadingSchedule(true);
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/schedule`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (response.ok) {
                const data = await response.json();
                setSchedule(data);
            }
        } catch (err) {
            console.error('Failed to fetch schedule:', err);
        } finally {
            setLoadingSchedule(false);
        }
    };

    const addTimeSlot = () => {
        setSchedule([...schedule, {
            day_of_week: 'monday',
            start_time: '09:00',
            end_time: '10:00'
        }]);
    };

    const removeTimeSlot = (index) => {
        setSchedule(schedule.filter((_, i) => i !== index));
    };

    const generateTimeOptions = () => {
        const options = [];
        for (let h = 0; h < 24; h++) {
            for (let m = 0; m < 60; m += 30) {
                const time = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
                const label = `${String(h % 12 || 12).padStart(2, '0')}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
                options.push({ value: time, label });
            }
        }
        return options;
    };

    const updateTimeSlot = (index, field, value) => {
        const updated = [...schedule];
        updated[index] = { ...updated[index], [field]: value };
        setSchedule(updated);
    };

    const saveSchedule = async () => {
        try {
            setSaving(true);
            setError(null);
            
            // Clean slots - remove appointment_type field that backend doesn't accept
            const cleanedSlots = schedule.map(({ day_of_week, start_time, end_time }) => ({
                day_of_week,
                start_time,
                end_time
            }));
            
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/schedule`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({ slots: cleanedSlots })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || 'Failed to save schedule');
            }
            
            setSuccess('✅ Schedule saved successfully!');
            setTimeout(() => setSuccess(null), 3000);
            
            // Don't refetch - backend replaces all slots, so our local state is already correct
            // Refetching would cause duplicates because of async timing
        } catch (err) {
            setError(err.message);
            setTimeout(() => setError(null), 5000);
        } finally {
            setSaving(false);
        }
    };

    const copyToClipboard = (text, field) => {
        navigator.clipboard.writeText(text);
        setCopied(field);
        setTimeout(() => setCopied(null), 2000);
    };

    const webhookUrl = `${window.location.origin.replace(':3000', ':8000')}/webhook/telegram/${settings.telegram_bot_token}`;
    const whatsappWebhookUrl = `${window.location.origin.replace(':3000', ':8000')}/webhook/whatsapp`;

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Success/Error Notifications */}
            {success && (
                <div className="fixed top-4 right-4 z-50 glass-card border-2 border-green-500/50 rounded-xl p-4 flex items-center gap-3 animate-fade-in">
                    <div className="w-10 h-10 bg-green-500/20 rounded-full flex items-center justify-center">
                        <Check className="text-green-400" size={20} />
                    </div>
                    <p className="text-white font-medium">{success}</p>
                </div>
            )}
            {error && (
                <div className="fixed top-4 right-4 z-50 glass-card border-2 border-red-500/50 rounded-xl p-4 flex items-center gap-3 animate-fade-in">
                    <div className="w-10 h-10 bg-red-500/20 rounded-full flex items-center justify-center">
                        <span className="text-red-400 text-xl">⚠</span>
                    </div>
                    <p className="text-white font-medium">{error}</p>
                </div>
            )}
            
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <SettingsIcon className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Account Settings</h2>
                        <p className="text-gray-400 text-sm">Configure your bots and profile</p>
                    </div>
                </div>
                
                <button
                    onClick={handleSave}
                    disabled={saving}
                    className="flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 px-4 py-2 rounded-lg font-semibold transition-colors disabled:opacity-50"
                >
                    {saving ? (
                        <div className="w-4 h-4 border-2 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
                    ) : (
                        <Save size={18} />
                    )}
                    Save Changes
                </button>
            </div>
            
            {/* Tabs */}
            <div className="flex gap-2 border-b border-white/10 pb-0">
                <button
                    onClick={() => setActiveTab('profile')}
                    className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                        activeTab === 'profile' 
                            ? 'text-gold-500 border-gold-500' 
                            : 'text-gray-400 border-transparent hover:text-white'
                    }`}
                >
                    <Building2 size={16} className="inline mr-2" />
                    Profile
                </button>
                <button
                    onClick={() => setActiveTab('bots')}
                    className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                        activeTab === 'bots' 
                            ? 'text-gold-500 border-gold-500' 
                            : 'text-gray-400 border-transparent hover:text-white'
                    }`}
                >
                    <Bot size={16} className="inline mr-2" />
                    Bots
                </button>
                <button
                    onClick={() => setActiveTab('schedule')}
                    className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                        activeTab === 'schedule' 
                            ? 'text-gold-500 border-gold-500' 
                            : 'text-gray-400 border-transparent hover:text-white'
                    }`}
                >
                    <Clock size={16} className="inline mr-2" />
                    Availability
                </button>
            </div>
            
            {/* Messages */}
            {error && (
                <div className="bg-red-500/20 border border-red-500 rounded-lg px-4 py-3 text-red-400">
                    {error}
                </div>
            )}
            {success && (
                <div className="bg-green-500/20 border border-green-500 rounded-lg px-4 py-3 text-green-400">
                    {success}
                </div>
            )}
            
            {/* Profile Tab Content */}
            {activeTab === 'profile' && (
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Building2 size={20} className="text-gold-500" />
                    Profile Information
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Your Name</label>
                        <input
                            type="text"
                            value={settings.name}
                            onChange={(e) => setSettings({ ...settings, name: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                            placeholder="Alexander Sterling"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Company Name</label>
                        <input
                            type="text"
                            value={settings.company_name}
                            onChange={(e) => setSettings({ ...settings, company_name: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                            placeholder="LuxeEstate Dubai"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2 flex items-center gap-2">
                            <Phone size={14} />
                            Phone
                        </label>
                        <input
                            type="tel"
                            value={settings.phone}
                            onChange={(e) => setSettings({ ...settings, phone: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                            placeholder="+971501234567"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2 flex items-center gap-2">
                            <Mail size={14} />
                            Email
                        </label>
                        <input
                            type="email"
                            value={settings.email}
                            onChange={(e) => setSettings({ ...settings, email: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                            placeholder="agent@luxeestate.ae"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2 flex items-center gap-2">
                            <Globe size={14} />
                            Logo URL
                        </label>
                        <input
                            type="url"
                            value={settings.logo_url}
                            onChange={(e) => setSettings({ ...settings, logo_url: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                            placeholder="https://example.com/logo.png"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2 flex items-center gap-2">
                            <Palette size={14} />
                            Primary Color
                        </label>
                        <div className="flex gap-2">
                            <input
                                type="color"
                                value={settings.primary_color}
                                onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                                className="w-12 h-12 rounded-lg border border-white/10 cursor-pointer"
                            />
                            <input
                                type="text"
                                value={settings.primary_color}
                                onChange={(e) => setSettings({ ...settings, primary_color: e.target.value })}
                                className="flex-1 bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none"
                                placeholder="#D4AF37"
                            />
                        </div>
                    </div>
                </div>
            </div>
            )}
            
            {/* Bots Tab Content */}
            {activeTab === 'bots' && (
            <>
            {/* Telegram Bot Section */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Bot size={20} className="text-blue-400" />
                    Telegram Bot Configuration
                </h3>
                
                <div className="space-y-4">
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Bot Token</label>
                        <div className="relative">
                            <input
                                type={showTelegramToken ? "text" : "password"}
                                value={settings.telegram_bot_token || currentTelegramToken}
                                onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                                className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 pr-12 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                                placeholder="123456789:ABCDefghIJKLmnopQRSTuvwxYZ"
                            />
                            <button
                                type="button"
                                onClick={() => setShowTelegramToken(!showTelegramToken)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                            >
                                {showTelegramToken ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                        <p className="text-gray-500 text-xs mt-2">
                            Get your bot token from <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-gold-500 hover:text-gold-400">@BotFather</a> on Telegram
                        </p>
                        {currentTelegramToken && !settings.telegram_bot_token && (
                            <p className="text-green-400 text-xs mt-1">✓ Token configured (hidden for security)</p>
                        )}
                    </div>
                    
                    {settings.telegram_bot_token && (
                        <div className="bg-navy-800 rounded-lg p-4">
                            <label className="text-gray-400 text-sm block mb-2">Webhook URL (Set this in BotFather)</label>
                            <div className="flex items-center gap-2">
                                <code className="flex-1 bg-navy-900 text-gold-500 px-3 py-2 rounded text-xs overflow-x-auto">
                                    {webhookUrl}
                                </code>
                                <button
                                    onClick={() => copyToClipboard(webhookUrl, 'telegram')}
                                    className="p-2 bg-navy-900 rounded hover:bg-gold-500 hover:text-navy-900 transition-colors"
                                >
                                    {copied === 'telegram' ? <Check size={16} /> : <Copy size={16} />}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
            
            {/* WhatsApp Section */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <MessageCircle size={20} className="text-green-400" />
                    WhatsApp Business API Configuration
                </h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Phone Number ID</label>
                        <input
                            type="text"
                            value={settings.whatsapp_phone_number_id}
                            onChange={(e) => setSettings({ ...settings, whatsapp_phone_number_id: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                            placeholder="123456789012345"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Business Account ID</label>
                        <input
                            type="text"
                            value={settings.whatsapp_business_account_id}
                            onChange={(e) => setSettings({ ...settings, whatsapp_business_account_id: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                            placeholder="987654321012345"
                        />
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Access Token</label>
                        <div className="relative">
                            <input
                                type={showWhatsAppToken ? "text" : "password"}
                                value={settings.whatsapp_access_token || currentWhatsAppToken}
                                onChange={(e) => setSettings({ ...settings, whatsapp_access_token: e.target.value })}
                                className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 pr-12 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                                placeholder="EAABx..."
                            />
                            <button
                                type="button"
                                onClick={() => setShowWhatsAppToken(!showWhatsAppToken)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors"
                            >
                                {showWhatsAppToken ? <EyeOff size={16} /> : <Eye size={16} />}
                            </button>
                        </div>
                        {currentWhatsAppToken && !settings.whatsapp_access_token && (
                            <p className="text-green-400 text-xs mt-1">✓ Token configured (hidden for security)</p>
                        )}
                    </div>
                    
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Verify Token (for webhook)</label>
                        <input
                            type="text"
                            value={settings.whatsapp_verify_token}
                            onChange={(e) => setSettings({ ...settings, whatsapp_verify_token: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                            placeholder="my_secure_verify_token"
                        />
                    </div>
                </div>
                
                <div className="bg-navy-800 rounded-lg p-4">
                    <label className="text-gray-400 text-sm block mb-2">Webhook URL (Set in Meta Business Manager)</label>
                    <div className="flex items-center gap-2">
                        <code className="flex-1 bg-navy-900 text-gold-500 px-3 py-2 rounded text-xs overflow-x-auto">
                            {whatsappWebhookUrl}
                        </code>
                        <button
                            onClick={() => copyToClipboard(whatsappWebhookUrl, 'whatsapp')}
                            className="p-2 bg-navy-900 rounded hover:bg-gold-500 hover:text-navy-900 transition-colors"
                        >
                            {copied === 'whatsapp' ? <Check size={16} /> : <Copy size={16} />}
                        </button>
                    </div>
                </div>
                
                <p className="text-gray-500 text-xs mt-4">
                    Get your WhatsApp Business API credentials from{' '}
                    <a 
                        href="https://business.facebook.com/" 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-gold-500 hover:text-gold-400 inline-flex items-center gap-1"
                    >
                        Meta Business Manager <ExternalLink size={12} />
                    </a>
                </p>
            </div>
            
            {/* WhatsApp Deep Link Section */}
            <div className="glass-card rounded-xl p-6 border-2 border-green-500/30">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <MessageCircle size={20} className="text-green-400" />
                    WhatsApp Shared Number (Deep Link)
                </h3>
                
                <div className="bg-navy-800 rounded-lg p-4 mb-4">
                    <p className="text-gray-400 text-sm mb-3">
                        💡 <strong className="text-white">Shared Number Mode:</strong> Use one WhatsApp number for all tenants. Users send messages to the shared number with a special link that identifies your agency.
                    </p>
                    
                    <div className="space-y-3">
                        <div>
                            <label className="text-gray-400 text-sm block mb-2">Your Deep Link</label>
                            <div className="flex items-center gap-2">
                                <code className="flex-1 bg-navy-900 text-green-400 px-3 py-2 rounded text-sm overflow-x-auto">
                                    https://wa.me/971501234567?text=TENANT_{tenantId}
                                </code>
                                <button
                                    onClick={() => copyToClipboard(`https://wa.me/971501234567?text=TENANT_${tenantId}`, 'deeplink')}
                                    className="p-2 bg-navy-900 rounded hover:bg-gold-500 hover:text-navy-900 transition-colors"
                                >
                                    {copied === 'deeplink' ? <Check size={16} /> : <Copy size={16} />}
                                </button>
                            </div>
                        </div>
                        
                        <div>
                            <label className="text-gray-400 text-sm block mb-2">QR Code Link</label>
                            <div className="flex items-center gap-2">
                                <code className="flex-1 bg-navy-900 text-green-400 px-3 py-2 rounded text-sm overflow-x-auto">
                                    https://api.qrserver.com/v1/create-qr-code/?data=https://wa.me/971501234567?text=TENANT_{tenantId}
                                </code>
                                <a
                                    href={`https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=https://wa.me/971501234567?text=TENANT_${tenantId}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="p-2 bg-navy-900 rounded hover:bg-gold-500 hover:text-navy-900 transition-colors"
                                    title="Download QR Code"
                                >
                                    <ExternalLink size={16} />
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                    <h4 className="text-green-400 font-medium mb-2">📱 How to Use:</h4>
                    <ol className="text-gray-400 text-sm space-y-2 list-decimal list-inside">
                        <li>Share the deep link or QR code with your clients</li>
                        <li>When they click it, WhatsApp opens with pre-filled text: <code className="text-green-400">TENANT_{tenantId}</code></li>
                        <li>System automatically routes the conversation to your dashboard</li>
                        <li>All leads are linked to your account (Tenant ID: {tenantId})</li>
                    </ol>
                </div>
            </div>
            
            {/* How It Works */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4">🤖 How Tenant Identification Works</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                    <div className="bg-navy-800 rounded-lg p-4">
                        <h4 className="text-blue-400 font-medium mb-2">Telegram</h4>
                        <p className="text-gray-400">
                            When a user sends a message to your bot, the system uses the <code className="text-gold-500">bot_token</code> from the webhook URL to identify which tenant owns this bot. All leads are automatically linked to your account.
                        </p>
                    </div>
                    <div className="bg-navy-800 rounded-lg p-4">
                        <h4 className="text-green-400 font-medium mb-2">WhatsApp</h4>
                        <p className="text-gray-400">
                            When a message arrives, the system uses the <code className="text-gold-500">phone_number_id</code> from the webhook payload to identify the tenant. Each agent has their own unique phone number.
                        </p>
                    </div>
                </div>
            </div>
            </>
            )}
            
            {/* Schedule Tab Content */}
            {activeTab === 'schedule' && (
            <div className="glass-card rounded-xl p-6">
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h3 className="text-white font-semibold flex items-center gap-2">
                            <Clock size={20} className="text-gold-500" />
                            Consultation Schedule
                        </h3>
                        <p className="text-gray-400 text-sm mt-1">Configure your weekly availability for client meetings</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={fetchSchedule}
                            disabled={loadingSchedule}
                            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors"
                            title="Load existing schedule from database"
                        >
                            <Clock size={16} />
                            {loadingSchedule ? 'Loading...' : 'Load Current Schedule'}
                        </button>
                        {schedule.length > 0 && (
                            <button
                                onClick={() => setSchedule([])}
                                className="flex items-center gap-2 bg-red-500/10 hover:bg-red-500/20 text-red-400 px-4 py-2 rounded-lg transition-colors border border-red-500/30"
                                title="Clear all slots"
                            >
                                <Trash2 size={16} />
                                Clear All
                            </button>
                        )}
                        <button
                            onClick={addTimeSlot}
                            className="flex items-center gap-2 bg-navy-800 hover:bg-navy-700 text-gold-500 px-4 py-2 rounded-lg transition-colors"
                        >
                            <Plus size={16} />
                            Add Time Slot
                        </button>
                    </div>
                </div>

                {loadingSchedule ? (
                    <div className="text-center py-8">
                        <div className="w-8 h-8 border-4 border-navy-800 border-t-gold-500 rounded-full animate-spin mx-auto"></div>
                    </div>
                ) : schedule.length === 0 ? (
                    <div className="text-center py-12 bg-navy-800/50 rounded-lg">
                        <Clock size={48} className="mx-auto text-gray-600 mb-3" />
                        <p className="text-gray-400">No time slots configured yet</p>
                        <p className="text-gray-500 text-sm mt-1">Click "Add Time Slot" to get started</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {schedule.map((slot, index) => (
                            <div key={index} className="bg-navy-800 rounded-lg p-4 flex items-center gap-4">
                                <select
                                    value={slot.day_of_week}
                                    onChange={(e) => updateTimeSlot(index, 'day_of_week', e.target.value)}
                                    className="bg-navy-900 text-white rounded px-3 py-2 border border-white/10"
                                >
                                    <option value="monday">Monday</option>
                                    <option value="tuesday">Tuesday</option>
                                    <option value="wednesday">Wednesday</option>
                                    <option value="thursday">Thursday</option>
                                    <option value="friday">Friday</option>
                                    <option value="saturday">Saturday</option>
                                    <option value="sunday">Sunday</option>
                                </select>

                                <select
                                    value={slot.start_time}
                                    onChange={(e) => updateTimeSlot(index, 'start_time', e.target.value)}
                                    className="bg-navy-900 text-white rounded px-3 py-2 border border-white/10"
                                >
                                    {generateTimeOptions().map(opt => (
                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>

                                <span className="text-gray-400">→</span>

                                <select
                                    value={slot.end_time}
                                    onChange={(e) => updateTimeSlot(index, 'end_time', e.target.value)}
                                    className="bg-navy-900 text-white rounded px-3 py-2 border border-white/10"
                                >
                                    {generateTimeOptions().map(opt => (
                                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>

                                <button
                                    onClick={() => removeTimeSlot(index)}
                                    className="ml-auto p-2 text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors"
                                    title="Remove slot"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}

                {schedule.length > 0 && (
                    <div className="mt-6 flex items-center gap-4">
                        <button
                            onClick={saveSchedule}
                            disabled={saving}
                            className="flex items-center gap-2 bg-gold-500 hover:bg-gold-600 text-navy-900 px-6 py-3 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {saving ? (
                                <>
                                    <div className="w-4 h-4 border-2 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
                                    Saving...
                                </>
                            ) : (
                                <>
                                    <Save size={18} />
                                    Save Schedule
                                </>
                            )}
                        </button>
                        <p className="text-gray-400 text-sm">
                            {schedule.length} time slot{schedule.length !== 1 ? 's' : ''} configured
                        </p>
                    </div>
                )}

                <div className="mt-6 bg-navy-800/50 rounded-lg p-4">
                    <p className="text-gray-400 text-sm">
                        💡 <strong className="text-white">Tip:</strong> These time slots will be shown to leads when they request a consultation. Make sure to keep them updated!
                    </p>
                </div>
            </div>
            )}
        </div>
    );

};

export default Settings;
