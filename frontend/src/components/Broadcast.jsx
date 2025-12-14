/**
 * Artin Smart Realty V2 - Broadcast Component
 * Send bulk messages to leads via Telegram/WhatsApp
 */

import React, { useState, useEffect } from 'react';
import { Send, Users, MessageSquare, Clock, CheckCircle2, XCircle, Loader } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const Broadcast = ({ tenantId }) => {
    const [leads, setLeads] = useState([]);
    const [selectedLeads, setSelectedLeads] = useState([]);
    const [message, setMessage] = useState('');
    const [platform, setPlatform] = useState('telegram'); // 'telegram' or 'whatsapp'
    const [sending, setSending] = useState(false);
    const [sendStatus, setSendStatus] = useState(null);
    const [filter, setFilter] = useState('all'); // 'all', 'new', 'qualified', 'contacted'

    useEffect(() => {
        loadLeads();
    }, [tenantId]);

    const loadLeads = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/leads`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            const data = await response.json();
            setLeads(data);
        } catch (error) {
            console.error('Failed to load leads:', error);
        }
    };

    const filteredLeads = leads.filter(lead => {
        if (filter === 'all') return true;
        return lead.status === filter;
    });

    const toggleLead = (leadId) => {
        if (selectedLeads.includes(leadId)) {
            setSelectedLeads(selectedLeads.filter(id => id !== leadId));
        } else {
            setSelectedLeads([...selectedLeads, leadId]);
        }
    };

    const selectAll = () => {
        if (selectedLeads.length === filteredLeads.length) {
            setSelectedLeads([]);
        } else {
            setSelectedLeads(filteredLeads.map(l => l.id));
        }
    };

    const sendBroadcast = async () => {
        if (!message.trim() || selectedLeads.length === 0) {
            alert('Please write a message and select at least one recipient');
            return;
        }

        setSending(true);
        setSendStatus(null);

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/broadcast`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    lead_ids: selectedLeads,
                    message: message,
                    platform: platform
                })
            });

            if (response.ok) {
                const result = await response.json();
                setSendStatus({
                    success: true,
                    sent: result.sent || selectedLeads.length,
                    failed: result.failed || 0
                });
                setMessage('');
                setSelectedLeads([]);
            } else {
                const error = await response.json();
                setSendStatus({
                    success: false,
                    error: error.detail || 'Failed to send broadcast'
                });
            }
        } catch (error) {
            console.error('Broadcast failed:', error);
            setSendStatus({
                success: false,
                error: error.message
            });
        } finally {
            setSending(false);
        }
    };

    const messageTemplates = [
        {
            title: 'New Property Alert',
            text: '🏠 New Listing Alert!\n\nWe have a new property that matches your preferences:\n\n📍 Location: [Location]\n💰 Price: [Price]\n🛏️ Bedrooms: [Beds]\n\nInterested? Reply or call us!'
        },
        {
            title: 'Price Drop',
            text: '🎉 Price Drop Alert!\n\nGreat news! The property you inquired about has a new price:\n\n📍 [Property Name]\n💰 New Price: [Price]\n✨ Save: [Discount]\n\nDon\'t miss this opportunity!'
        },
        {
            title: 'Viewing Reminder',
            text: '📅 Viewing Reminder\n\nThis is a reminder for your property viewing:\n\n🏠 Property: [Name]\n📍 Location: [Location]\n🕐 Time: [Time]\n\nSee you there!'
        },
        {
            title: 'Follow-up',
            text: 'Hi [Name]! 👋\n\nJust checking in to see if you\'re still interested in finding your dream property in Dubai.\n\nWe have some great new listings that match your criteria.\n\nWould you like to schedule a viewing?'
        }
    ];

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <Send className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Broadcast Messages</h2>
                        <p className="text-gray-400 text-sm">Send bulk messages to your leads</p>
                    </div>
                </div>
                <div className="flex items-center gap-2 bg-navy-800 rounded-lg px-4 py-2">
                    <Users size={16} className="text-gold-500" />
                    <span className="text-white font-semibold">{selectedLeads.length}</span>
                    <span className="text-gray-400 text-sm">selected</span>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Panel - Recipients */}
                <div className="lg:col-span-1 glass-card rounded-xl p-6 space-y-4">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-white font-semibold">Recipients</h3>
                        <button
                            onClick={selectAll}
                            className="text-gold-500 hover:text-gold-400 text-sm"
                        >
                            {selectedLeads.length === filteredLeads.length ? 'Deselect All' : 'Select All'}
                        </button>
                    </div>

                    {/* Filter */}
                    <select
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/10 outline-none"
                    >
                        <option value="all">All Leads ({leads.length})</option>
                        <option value="new">New Leads</option>
                        <option value="qualified">Qualified</option>
                        <option value="contacted">Contacted</option>
                    </select>

                    {/* Leads List */}
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {filteredLeads.map(lead => (
                            <label
                                key={lead.id}
                                className="flex items-center gap-3 p-3 bg-navy-800 rounded-lg cursor-pointer hover:bg-navy-700 transition-colors"
                            >
                                <input
                                    type="checkbox"
                                    checked={selectedLeads.includes(lead.id)}
                                    onChange={() => toggleLead(lead.id)}
                                    className="w-4 h-4 rounded border-gray-600 text-gold-500 focus:ring-gold-500"
                                />
                                <div className="flex-1">
                                    <p className="text-white text-sm font-medium">{lead.name || 'Anonymous'}</p>
                                    <p className="text-gray-400 text-xs">{lead.phone || 'No phone'}</p>
                                </div>
                                <span className={`text-xs px-2 py-1 rounded ${
                                    lead.status === 'new' ? 'bg-red-500/20 text-red-400' :
                                    lead.status === 'qualified' ? 'bg-green-500/20 text-green-400' :
                                    'bg-gray-500/20 text-gray-400'
                                }`}>
                                    {lead.status || 'new'}
                                </span>
                            </label>
                        ))}

                        {filteredLeads.length === 0 && (
                            <div className="text-center py-8">
                                <Users className="text-gray-600 mx-auto mb-2" size={32} />
                                <p className="text-gray-500 text-sm">No leads found</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel - Message Composer */}
                <div className="lg:col-span-2 glass-card rounded-xl p-6 space-y-6">
                    <h3 className="text-white font-semibold">Compose Message</h3>

                    {/* Platform Selection */}
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Send via</label>
                        <div className="flex gap-3">
                            <button
                                onClick={() => setPlatform('telegram')}
                                className={`flex-1 p-3 rounded-lg border-2 transition-all ${
                                    platform === 'telegram'
                                        ? 'border-gold-500 bg-gold-500/10'
                                        : 'border-white/10 hover:border-gold-500/30'
                                }`}
                            >
                                <MessageSquare className="text-gold-500 mx-auto mb-2" size={24} />
                                <p className="text-white text-sm">Telegram</p>
                            </button>
                            <button
                                onClick={() => setPlatform('whatsapp')}
                                className={`flex-1 p-3 rounded-lg border-2 transition-all ${
                                    platform === 'whatsapp'
                                        ? 'border-gold-500 bg-gold-500/10'
                                        : 'border-white/10 hover:border-gold-500/30'
                                }`}
                            >
                                <MessageSquare className="text-gold-500 mx-auto mb-2" size={24} />
                                <p className="text-white text-sm">WhatsApp</p>
                            </button>
                        </div>
                    </div>

                    {/* Message Templates */}
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Quick Templates</label>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {messageTemplates.map((template, index) => (
                                <button
                                    key={index}
                                    onClick={() => setMessage(template.text)}
                                    className="text-left p-3 bg-navy-800 hover:bg-navy-700 rounded-lg border border-white/10 transition-colors"
                                >
                                    <p className="text-white text-sm font-medium">{template.title}</p>
                                    <p className="text-gray-400 text-xs mt-1 line-clamp-2">{template.text}</p>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Message Input */}
                    <div>
                        <label className="text-gray-400 text-sm block mb-2">Message</label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            placeholder="Write your message here... You can use placeholders like [Name], [Location], [Price]"
                            rows={8}
                            className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none resize-none"
                        />
                        <p className="text-gray-500 text-xs mt-2">{message.length} characters</p>
                    </div>

                    {/* Send Status */}
                    {sendStatus && (
                        <div className={`p-4 rounded-lg border ${
                            sendStatus.success
                                ? 'bg-green-500/10 border-green-500/30'
                                : 'bg-red-500/10 border-red-500/30'
                        }`}>
                            <div className="flex items-center gap-2">
                                {sendStatus.success ? (
                                    <>
                                        <CheckCircle2 className="text-green-400" size={20} />
                                        <div>
                                            <p className="text-green-400 font-medium">Broadcast Sent!</p>
                                            <p className="text-green-400/80 text-sm">
                                                Successfully sent to {sendStatus.sent} recipients
                                                {sendStatus.failed > 0 && ` (${sendStatus.failed} failed)`}
                                            </p>
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <XCircle className="text-red-400" size={20} />
                                        <div>
                                            <p className="text-red-400 font-medium">Failed to Send</p>
                                            <p className="text-red-400/80 text-sm">{sendStatus.error}</p>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Send Button */}
                    <button
                        onClick={sendBroadcast}
                        disabled={sending || !message.trim() || selectedLeads.length === 0}
                        className="w-full bg-gold-500 hover:bg-gold-400 disabled:bg-gray-600 disabled:cursor-not-allowed text-navy-900 font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                        {sending ? (
                            <>
                                <Loader className="animate-spin" size={20} />
                                Sending...
                            </>
                        ) : (
                            <>
                                <Send size={20} />
                                Send to {selectedLeads.length} Lead{selectedLeads.length !== 1 ? 's' : ''}
                            </>
                        )}
                    </button>

                    {/* Warning */}
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                        <p className="text-yellow-400 text-sm">
                            ⚠️ <strong>Note:</strong> Make sure you have proper consent from recipients before sending bulk messages.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Broadcast;
