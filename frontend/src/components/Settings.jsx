/**
 * ArtinSmartRealty V2 - Settings Page
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
    ExternalLink
} from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Settings = ({ tenantId, token }) => {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    const [copied, setCopied] = useState(null);
    
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
            
            // Note: We would need a PUT endpoint for updating tenant settings
            // For now, this is a placeholder
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
            
            {/* Profile Section */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Building2 size={20} className="text-gold-500" />
                    Profile Information
                </h3>
                
                <div className="grid grid-cols-2 gap-4">
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
            
            {/* Telegram Bot Section */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                    <Bot size={20} className="text-blue-400" />
                    Telegram Bot Configuration
                </h3>
                
                <div className="space-y-4">
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Bot Token</label>
                        <input
                            type="text"
                            value={settings.telegram_bot_token}
                            onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                            placeholder="123456789:ABCDefghIJKLmnopQRSTuvwxYZ"
                        />
                        <p className="text-gray-500 text-xs mt-2">
                            Get your bot token from <a href="https://t.me/BotFather" target="_blank" rel="noopener noreferrer" className="text-gold-500 hover:text-gold-400">@BotFather</a> on Telegram
                        </p>
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
                
                <div className="grid grid-cols-2 gap-4 mb-4">
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
                        <input
                            type="password"
                            value={settings.whatsapp_access_token}
                            onChange={(e) => setSettings({ ...settings, whatsapp_access_token: e.target.value })}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none font-mono text-sm"
                            placeholder="EAABx..."
                        />
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
            
            {/* How It Works */}
            <div className="glass-card rounded-xl p-6">
                <h3 className="text-white font-semibold mb-4">🤖 How Tenant Identification Works</h3>
                <div className="grid grid-cols-2 gap-6 text-sm">
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
        </div>
    );
};

export default Settings;
