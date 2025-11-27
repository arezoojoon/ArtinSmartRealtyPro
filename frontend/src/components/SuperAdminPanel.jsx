/**
 * Super Admin Panel - Tenant Management
 * Admin can create tenants, manage subscriptions, collect payments
 */

import React, { useState, useEffect } from 'react';
import {
    Users,
    Plus,
    Edit,
    Trash2,
    DollarSign,
    CreditCard,
    CheckCircle,
    XCircle,
    Clock,
    Search
} from 'lucide-react';

const API_BASE_URL = window.ENV?.VITE_API_URL || import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const SuperAdminPanel = () => {
    const [tenants, setTenants] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [editingTenant, setEditingTenant] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        company_name: '',
        phone: '',
        telegram_bot_token: '',
        subscription_status: 'TRIAL',
        payment_method: 'CASH',
        payment_amount: 0
    });

    useEffect(() => {
        loadTenants();
    }, []);

    const loadTenants = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/admin/tenants`, {
                headers: getAuthHeaders(),
            });
            const data = await response.json();
            setTenants(data);
        } catch (error) {
            console.error('Failed to load tenants:', error);
            alert('خطا در بارگذاری لیست تنانت‌ها');
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const url = editingTenant
                ? `${API_BASE_URL}/api/admin/tenants/${editingTenant.id}`
                : `${API_BASE_URL}/api/admin/tenants`;
            
            const method = editingTenant ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders(),
                },
                body: JSON.stringify(formData),
            });

            if (response.ok) {
                await loadTenants();
                closeModal();
                alert(editingTenant ? 'تنانت با موفقیت ویرایش شد!' : 'تنانت جدید ایجاد شد!');
            } else {
                const error = await response.json();
                alert(`خطا: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to save tenant:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('آیا مطمئن هستید می‌خواهید این تنانت را حذف کنید؟')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/admin/tenants/${id}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });

            if (response.ok) {
                await loadTenants();
                alert('تنانت حذف شد');
            } else {
                alert('خطا در حذف تنانت');
            }
        } catch (error) {
            console.error('Failed to delete tenant:', error);
        }
    };

    const openModal = (tenant = null) => {
        setEditingTenant(tenant);
        if (tenant) {
            setFormData({
                name: tenant.name || '',
                email: tenant.email || '',
                password: '',
                company_name: tenant.company_name || '',
                phone: tenant.phone || '',
                telegram_bot_token: tenant.telegram_bot_token || '',
                subscription_status: tenant.subscription_status || 'TRIAL',
                payment_method: 'CASH',
                payment_amount: 0
            });
        } else {
            setFormData({
                name: '',
                email: '',
                password: '',
                company_name: '',
                phone: '',
                telegram_bot_token: '',
                subscription_status: 'TRIAL',
                payment_method: 'CASH',
                payment_amount: 0
            });
        }
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingTenant(null);
    };

    const getStatusBadge = (status) => {
        const colors = {
            TRIAL: 'bg-blue-500',
            ACTIVE: 'bg-green-500',
            SUSPENDED: 'bg-yellow-500',
            CANCELLED: 'bg-red-500'
        };
        return (
            <span className={`${colors[status]} text-white px-2 py-1 rounded text-xs`}>
                {status}
            </span>
        );
    };

    const filteredTenants = tenants.filter(t =>
        t.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        t.company_name?.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#0f1729] via-[#1a2332] to-[#0f1729] p-6">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
                    <Users className="text-[#D4AF37]" size={32} />
                    مدیریت تنانت‌ها
                </h1>
                <p className="text-gray-400">مدیریت کاربران و اشتراک‌ها</p>
            </div>

            {/* Controls */}
            <div className="flex justify-between items-center mb-6">
                <div className="relative flex-1 max-w-md">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
                    <input
                        type="text"
                        placeholder="جستجو..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="w-full bg-[#1a2332] border border-gray-700 rounded-lg pl-10 pr-4 py-2 text-white focus:outline-none focus:border-[#D4AF37]"
                    />
                </div>
                <button
                    onClick={() => openModal()}
                    className="bg-[#D4AF37] hover:bg-[#c99d2e] text-[#0f1729] font-semibold px-6 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                    <Plus size={20} />
                    تنانت جدید
                </button>
            </div>

            {/* Tenants Table */}
            {loading ? (
                <div className="text-center text-gray-400 py-12">در حال بارگذاری...</div>
            ) : filteredTenants.length === 0 ? (
                <div className="text-center text-gray-400 py-12">
                    هیچ تنانتی یافت نشد
                </div>
            ) : (
                <div className="bg-[#1a2332] rounded-lg overflow-hidden border border-gray-700">
                    <table className="w-full">
                        <thead className="bg-[#0f1729]">
                            <tr>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">نام</th>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">ایمیل</th>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">شرکت</th>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">وضعیت</th>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">تاریخ ثبت</th>
                                <th className="px-6 py-4 text-right text-[#D4AF37]">عملیات</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredTenants.map((tenant) => (
                                <tr key={tenant.id} className="border-t border-gray-700 hover:bg-[#0f1729]/50">
                                    <td className="px-6 py-4 text-white">{tenant.name}</td>
                                    <td className="px-6 py-4 text-gray-300">{tenant.email}</td>
                                    <td className="px-6 py-4 text-gray-300">{tenant.company_name || '-'}</td>
                                    <td className="px-6 py-4">{getStatusBadge(tenant.subscription_status)}</td>
                                    <td className="px-6 py-4 text-gray-400">
                                        {new Date(tenant.created_at).toLocaleDateString('fa-IR')}
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => openModal(tenant)}
                                                className="text-blue-400 hover:text-blue-300"
                                            >
                                                <Edit size={18} />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(tenant.id)}
                                                className="text-red-400 hover:text-red-300"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-[#1a2332] rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-gray-700 flex justify-between items-center">
                            <h2 className="text-2xl font-bold text-white">
                                {editingTenant ? 'ویرایش تنانت' : 'تنانت جدید'}
                            </h2>
                            <button onClick={closeModal} className="text-gray-400 hover:text-white">
                                <XCircle size={24} />
                            </button>
                        </div>
                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-gray-300 mb-2">نام *</label>
                                    <input
                                        type="text"
                                        required
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-gray-300 mb-2">ایمیل *</label>
                                    <input
                                        type="email"
                                        required
                                        value={formData.email}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                            </div>

                            {!editingTenant && (
                                <div>
                                    <label className="block text-gray-300 mb-2">رمز عبور *</label>
                                    <input
                                        type="password"
                                        required
                                        value={formData.password}
                                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-gray-300 mb-2">نام شرکت</label>
                                    <input
                                        type="text"
                                        value={formData.company_name}
                                        onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                                <div>
                                    <label className="block text-gray-300 mb-2">تلفن</label>
                                    <input
                                        type="text"
                                        value={formData.phone}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-gray-300 mb-2">Telegram Bot Token</label>
                                <input
                                    type="text"
                                    value={formData.telegram_bot_token}
                                    onChange={(e) => setFormData({ ...formData, telegram_bot_token: e.target.value })}
                                    className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                />
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-gray-300 mb-2">وضعیت اشتراک</label>
                                    <select
                                        value={formData.subscription_status}
                                        onChange={(e) => setFormData({ ...formData, subscription_status: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    >
                                        <option value="TRIAL">Trial</option>
                                        <option value="ACTIVE">Active</option>
                                        <option value="SUSPENDED">Suspended</option>
                                        <option value="CANCELLED">Cancelled</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-gray-300 mb-2">روش پرداخت</label>
                                    <select
                                        value={formData.payment_method}
                                        onChange={(e) => setFormData({ ...formData, payment_method: e.target.value })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    >
                                        <option value="CASH">نقدی</option>
                                        <option value="ONLINE">آنلاین</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-gray-300 mb-2">مبلغ (تومان)</label>
                                    <input
                                        type="number"
                                        value={formData.payment_amount}
                                        onChange={(e) => setFormData({ ...formData, payment_amount: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-[#0f1729] border border-gray-700 rounded px-4 py-2 text-white"
                                    />
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700"
                                >
                                    انصراف
                                </button>
                                <button
                                    type="submit"
                                    className="px-6 py-2 bg-[#D4AF37] hover:bg-[#c99d2e] text-[#0f1729] font-semibold rounded-lg"
                                >
                                    {editingTenant ? 'ذخیره تغییرات' : 'ایجاد تنانت'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SuperAdminPanel;
