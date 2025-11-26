/**
 * ArtinSmartRealty V2 - Login & Register Page
 * Authentication for Tenant (Agent) Dashboard
 */

import React, { useState } from 'react';
import { Building2, Eye, EyeOff, ArrowRight, UserPlus, LogIn } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Login = ({ onLogin }) => {
    const [mode, setMode] = useState('login'); // 'login' | 'register' | 'forgot'
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [success, setSuccess] = useState(null);
    
    // Form fields
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [name, setName] = useState('');
    const [companyName, setCompanyName] = useState('');
    const [phone, setPhone] = useState('');

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Login failed');
            }
            
            const data = await response.json();
            
            // Store token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('tenantId', data.tenant_id);
            localStorage.setItem('userName', data.name);
            localStorage.setItem('userEmail', data.email);
            
            onLogin(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name,
                    email,
                    password,
                    company_name: companyName,
                    phone,
                }),
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Registration failed');
            }
            
            const data = await response.json();
            
            // Store token and user info
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('tenantId', data.tenant_id);
            localStorage.setItem('userName', data.name);
            localStorage.setItem('userEmail', data.email);
            
            onLogin(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleForgotPassword = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setSuccess(null);
        
        try {
            const response = await fetch(`${API_BASE_URL}/api/auth/forgot-password`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email }),
            });
            
            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Request failed');
            }
            
            setSuccess('If the email exists, a password reset link has been sent.');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-navy-900 flex items-center justify-center p-4">
            {/* Background decoration */}
            <div className="absolute inset-0 overflow-hidden">
                <div className="absolute -top-40 -right-40 w-96 h-96 bg-gold-500/10 rounded-full blur-3xl"></div>
                <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-gold-500/10 rounded-full blur-3xl"></div>
            </div>
            
            <div className="relative z-10 w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-gold-500 to-gold-600 rounded-xl mb-4">
                        <Building2 className="text-navy-900" size={32} />
                    </div>
                    <h1 className="text-2xl font-bold text-white">ArtinSmartRealty</h1>
                    <p className="text-gray-400 text-sm mt-1">Real Estate SaaS Platform</p>
                </div>
                
                {/* Card */}
                <div className="glass-card rounded-2xl p-8">
                    {/* Tabs */}
                    {mode !== 'forgot' && (
                        <div className="flex bg-navy-800 rounded-lg p-1 mb-6">
                            <button
                                onClick={() => setMode('login')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-colors ${
                                    mode === 'login' 
                                        ? 'bg-gold-500 text-navy-900' 
                                        : 'text-gray-400 hover:text-white'
                                }`}
                            >
                                <LogIn size={16} />
                                Login
                            </button>
                            <button
                                onClick={() => setMode('register')}
                                className={`flex-1 flex items-center justify-center gap-2 py-2 rounded-md text-sm font-medium transition-colors ${
                                    mode === 'register' 
                                        ? 'bg-gold-500 text-navy-900' 
                                        : 'text-gray-400 hover:text-white'
                                }`}
                            >
                                <UserPlus size={16} />
                                Register
                            </button>
                        </div>
                    )}
                    
                    {/* Error/Success Messages */}
                    {error && (
                        <div className="bg-red-500/20 border border-red-500 rounded-lg px-4 py-3 mb-4 text-red-400 text-sm">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="bg-green-500/20 border border-green-500 rounded-lg px-4 py-3 mb-4 text-green-400 text-sm">
                            {success}
                        </div>
                    )}
                    
                    {/* Login Form */}
                    {mode === 'login' && (
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="agent@example.com"
                                />
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Password</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors pr-12"
                                        placeholder="••••••••"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>
                            
                            <div className="flex justify-end">
                                <button
                                    type="button"
                                    onClick={() => setMode('forgot')}
                                    className="text-gold-500 text-sm hover:text-gold-400"
                                >
                                    Forgot password?
                                </button>
                            </div>
                            
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        Login to Dashboard
                                        <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                        </form>
                    )}
                    
                    {/* Register Form */}
                    {mode === 'register' && (
                        <form onSubmit={handleRegister} className="space-y-4">
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Your Name</label>
                                <input
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="Alexander Sterling"
                                />
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Company Name (Optional)</label>
                                <input
                                    type="text"
                                    value={companyName}
                                    onChange={(e) => setCompanyName(e.target.value)}
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="LuxeEstate Dubai"
                                />
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="agent@example.com"
                                />
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Phone (Optional)</label>
                                <input
                                    type="tel"
                                    value={phone}
                                    onChange={(e) => setPhone(e.target.value)}
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="+971501234567"
                                />
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Password</label>
                                <div className="relative">
                                    <input
                                        type={showPassword ? 'text' : 'password'}
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                        minLength={6}
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors pr-12"
                                        placeholder="••••••••"
                                    />
                                    <button
                                        type="button"
                                        onClick={() => setShowPassword(!showPassword)}
                                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white"
                                    >
                                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                    </button>
                                </div>
                            </div>
                            
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                    <>
                                        Create Account
                                        <ArrowRight size={18} />
                                    </>
                                )}
                            </button>
                            
                            <p className="text-center text-gray-500 text-xs mt-4">
                                Free 14-day trial • No credit card required
                            </p>
                        </form>
                    )}
                    
                    {/* Forgot Password Form */}
                    {mode === 'forgot' && (
                        <form onSubmit={handleForgotPassword} className="space-y-4">
                            <div className="text-center mb-4">
                                <h2 className="text-white font-semibold mb-2">Reset Password</h2>
                                <p className="text-gray-400 text-sm">Enter your email to receive a reset link</p>
                            </div>
                            
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Email</label>
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 focus:border-gold-500 outline-none transition-colors"
                                    placeholder="agent@example.com"
                                />
                            </div>
                            
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 font-semibold py-3 rounded-lg transition-colors disabled:opacity-50"
                            >
                                {loading ? (
                                    <div className="w-5 h-5 border-2 border-navy-900 border-t-transparent rounded-full animate-spin"></div>
                                ) : (
                                    'Send Reset Link'
                                )}
                            </button>
                            
                            <button
                                type="button"
                                onClick={() => setMode('login')}
                                className="w-full text-gray-400 hover:text-white text-sm py-2"
                            >
                                ← Back to Login
                            </button>
                        </form>
                    )}
                </div>
                
                {/* Footer */}
                <p className="text-center text-gray-600 text-xs mt-8">
                    © 2024 ArtinSmartRealty. All rights reserved.
                </p>
            </div>
        </div>
    );
};

export default Login;
