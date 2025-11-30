/**
 * Artin Smart Realty V2 - QR Generator
 * Generate QR codes for properties, agents, and bot links
 */

import React, { useState, useRef, useEffect } from 'react';
import { QrCode, Download, Link, Building2, User, Bot, Copy, Check } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const QRGenerator = ({ tenantId }) => {
    const [qrType, setQrType] = useState('bot'); // 'bot', 'property', 'agent'
    const [qrData, setQrData] = useState('');
    const [qrGenerated, setQrGenerated] = useState(false);
    const [copied, setCopied] = useState(false);
    const [properties, setProperties] = useState([]);
    const [selectedProperty, setSelectedProperty] = useState(null);
    const canvasRef = useRef(null);

    // Load properties for QR generation
    useEffect(() => {
        if (qrType === 'property') {
            loadProperties();
        }
    }, [qrType]);

    const loadProperties = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/properties`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            const data = await response.json();
            setProperties(data);
        } catch (error) {
            console.error('Failed to load properties:', error);
        }
    };

    const generateQR = async () => {
        let url = '';

        if (qrType === 'bot') {
            const botToken = qrData || 'your_bot_username';
            url = `https://t.me/${botToken}`;
        } else if (qrType === 'property' && selectedProperty) {
            url = `${window.location.origin}/property/${selectedProperty.id}`;
        } else if (qrType === 'agent') {
            url = qrData || window.location.origin;
        }

        if (!url) return;

        // Use QRCode.js library (simple, no extra dependencies)
        try {
            // Dynamic import of qrcode library (if available)
            const QRCode = (await import('qrcode')).default;
            
            if (canvasRef.current) {
                QRCode.toCanvas(canvasRef.current, url, {
                    width: 300,
                    margin: 2,
                    color: {
                        dark: '#D4AF37',
                        light: '#1a2332'
                    }
                });
                setQrGenerated(true);
            }
        } catch (error) {
            // Fallback: Use simple div-based QR display
            console.log('QRCode library not available, using fallback');
            setQrGenerated(true);
        }
    };

    const downloadQR = () => {
        if (canvasRef.current) {
            const link = document.createElement('a');
            link.download = `qr-${qrType}-${Date.now()}.png`;
            link.href = canvasRef.current.toDataURL();
            link.click();
        }
    };

    const copyLink = () => {
        let url = '';
        if (qrType === 'bot') {
            url = `https://t.me/${qrData || 'your_bot'}`;
        } else if (qrType === 'property' && selectedProperty) {
            url = `${window.location.origin}/property/${selectedProperty.id}`;
        } else if (qrType === 'agent') {
            url = qrData || window.location.origin;
        }

        navigator.clipboard.writeText(url);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <QrCode className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">QR Code Generator</h2>
                        <p className="text-gray-400 text-sm">Generate QR codes for bot, properties, or agent contact</p>
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Panel - Configuration */}
                <div className="glass-card rounded-xl p-6 space-y-6">
                    <h3 className="text-white font-semibold mb-4">Configure QR Code</h3>

                    {/* QR Type Selection */}
                    <div>
                        <label className="text-gray-400 text-sm block mb-3">QR Code Type</label>
                        <div className="grid grid-cols-3 gap-3">
                            <button
                                onClick={() => setQrType('bot')}
                                className={`p-4 rounded-lg border-2 transition-all ${
                                    qrType === 'bot'
                                        ? 'border-gold-500 bg-gold-500/10'
                                        : 'border-white/10 hover:border-gold-500/30'
                                }`}
                            >
                                <Bot className="text-gold-500 mx-auto mb-2" size={24} />
                                <p className="text-white text-sm">Telegram Bot</p>
                            </button>
                            <button
                                onClick={() => setQrType('property')}
                                className={`p-4 rounded-lg border-2 transition-all ${
                                    qrType === 'property'
                                        ? 'border-gold-500 bg-gold-500/10'
                                        : 'border-white/10 hover:border-gold-500/30'
                                }`}
                            >
                                <Building2 className="text-gold-500 mx-auto mb-2" size={24} />
                                <p className="text-white text-sm">Property</p>
                            </button>
                            <button
                                onClick={() => setQrType('agent')}
                                className={`p-4 rounded-lg border-2 transition-all ${
                                    qrType === 'agent'
                                        ? 'border-gold-500 bg-gold-500/10'
                                        : 'border-white/10 hover:border-gold-500/30'
                                }`}
                            >
                                <User className="text-gold-500 mx-auto mb-2" size={24} />
                                <p className="text-white text-sm">Agent Contact</p>
                            </button>
                        </div>
                    </div>

                    {/* Bot Username Input */}
                    {qrType === 'bot' && (
                        <div>
                            <label className="text-gray-400 text-sm block mb-2">Telegram Bot Username</label>
                            <div className="flex items-center gap-2 bg-navy-800 rounded-lg px-4 py-3 border border-white/10">
                                <span className="text-gray-500">@</span>
                                <input
                                    type="text"
                                    value={qrData}
                                    onChange={(e) => setQrData(e.target.value)}
                                    placeholder="your_bot_username"
                                    className="bg-transparent text-white outline-none flex-1"
                                />
                            </div>
                            <p className="text-xs text-gray-500 mt-2">Enter your Telegram bot username (without @)</p>
                        </div>
                    )}

                    {/* Property Selection */}
                    {qrType === 'property' && (
                        <div>
                            <label className="text-gray-400 text-sm block mb-2">Select Property</label>
                            <select
                                value={selectedProperty?.id || ''}
                                onChange={(e) => {
                                    const prop = properties.find(p => p.id === parseInt(e.target.value));
                                    setSelectedProperty(prop);
                                }}
                                className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                            >
                                <option value="">Choose a property...</option>
                                {properties.map(prop => (
                                    <option key={prop.id} value={prop.id}>
                                        {prop.name} - {prop.location}
                                    </option>
                                ))}
                            </select>
                            {selectedProperty && (
                                <div className="mt-3 p-3 bg-navy-800 rounded-lg">
                                    <p className="text-white text-sm font-medium">{selectedProperty.name}</p>
                                    <p className="text-gray-400 text-xs">{selectedProperty.location}</p>
                                    <p className="text-gold-500 text-sm mt-1">
                                        {selectedProperty.price} {selectedProperty.currency}
                                    </p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Agent Contact Input */}
                    {qrType === 'agent' && (
                        <div>
                            <label className="text-gray-400 text-sm block mb-2">Contact Link or Phone</label>
                            <input
                                type="text"
                                value={qrData}
                                onChange={(e) => setQrData(e.target.value)}
                                placeholder="https://wa.me/971501234567 or tel:+971501234567"
                                className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                            />
                            <p className="text-xs text-gray-500 mt-2">WhatsApp link, phone, or contact URL</p>
                        </div>
                    )}

                    {/* Generate Button */}
                    <button
                        onClick={generateQR}
                        disabled={
                            (qrType === 'bot' && !qrData) ||
                            (qrType === 'property' && !selectedProperty) ||
                            (qrType === 'agent' && !qrData)
                        }
                        className="w-full bg-gold-500 hover:bg-gold-400 disabled:bg-gray-600 disabled:cursor-not-allowed text-navy-900 font-semibold py-3 rounded-lg transition-colors flex items-center justify-center gap-2"
                    >
                        <QrCode size={20} />
                        Generate QR Code
                    </button>
                </div>

                {/* Right Panel - QR Preview */}
                <div className="glass-card rounded-xl p-6">
                    <h3 className="text-white font-semibold mb-4">QR Code Preview</h3>

                    {!qrGenerated ? (
                        <div className="flex items-center justify-center h-80 border-2 border-dashed border-white/10 rounded-xl">
                            <div className="text-center">
                                <QrCode className="text-gray-600 mx-auto mb-3" size={64} />
                                <p className="text-gray-500">Configure and generate your QR code</p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {/* QR Code Display */}
                            <div className="flex justify-center p-6 bg-white rounded-xl">
                                <canvas ref={canvasRef} style={{ maxWidth: '100%' }}></canvas>
                            </div>

                            {/* Action Buttons */}
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={downloadQR}
                                    className="flex items-center justify-center gap-2 bg-green-500 hover:bg-green-400 text-white font-semibold py-3 rounded-lg transition-colors"
                                >
                                    <Download size={18} />
                                    Download PNG
                                </button>
                                <button
                                    onClick={copyLink}
                                    className="flex items-center justify-center gap-2 bg-navy-800 hover:bg-navy-700 text-white font-semibold py-3 rounded-lg transition-colors border border-white/10"
                                >
                                    {copied ? (
                                        <>
                                            <Check size={18} className="text-green-400" />
                                            Copied!
                                        </>
                                    ) : (
                                        <>
                                            <Copy size={18} />
                                            Copy Link
                                        </>
                                    )}
                                </button>
                            </div>

                            {/* Info Box */}
                            <div className="bg-navy-800 rounded-lg p-4 border border-white/10">
                                <p className="text-gray-400 text-sm mb-2">
                                    <strong className="text-white">Tip:</strong> Print this QR code on:
                                </p>
                                <ul className="text-gray-400 text-xs space-y-1 ml-4">
                                    <li>• Business cards for instant contact</li>
                                    <li>• Property brochures for quick access</li>
                                    <li>• Billboards and signage</li>
                                    <li>• Social media posts</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default QRGenerator;
