/**
 * Artin Smart Realty V2 - Lottery System
 * Create and manage giveaways and lottery campaigns
 */

import React, { useState, useEffect } from 'react';
import { Gift, Plus, Edit, Trash2, X, Users, Calendar, Trophy, Play, Pause } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const Lottery = ({ tenantId }) => {
    const [lotteries, setLotteries] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [editingLottery, setEditingLottery] = useState(null);
    const [showWinnerModal, setShowWinnerModal] = useState(false);
    const [selectedWinner, setSelectedWinner] = useState(null);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        prize: '',
        start_date: '',
        end_date: '',
        max_participants: '',
        status: 'active'
    });

    useEffect(() => {
        loadLotteries();
    }, [tenantId]);

    const loadLotteries = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/lotteries`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            
            if (response.ok) {
                const data = await response.json();
                setLotteries(data);
            } else {
                // Mock data for demo
                setLotteries([
                    {
                        id: 1,
                        title: 'New Year Villa Giveaway',
                        description: 'Win a luxury villa worth $2M!',
                        prize: 'Luxury Villa in Palm Jumeirah',
                        start_date: '2025-01-01',
                        end_date: '2025-01-31',
                        participants: 234,
                        max_participants: 500,
                        status: 'active',
                        winner: null
                    },
                    {
                        id: 2,
                        title: 'Golden Ticket Campaign',
                        description: 'Free consultation + 10% discount',
                        prize: 'Consultation Package',
                        start_date: '2024-12-01',
                        end_date: '2024-12-31',
                        participants: 456,
                        max_participants: 1000,
                        status: 'completed',
                        winner: { name: 'Ahmed Mohammed', phone: '+971501234567' }
                    }
                ]);
            }
        } catch (error) {
            console.error('Failed to load lotteries:', error);
        }
    };

    const openModal = (lottery = null) => {
        if (lottery) {
            setEditingLottery(lottery);
            setFormData({
                title: lottery.title || '',
                description: lottery.description || '',
                prize: lottery.prize || '',
                start_date: lottery.start_date || '',
                end_date: lottery.end_date || '',
                max_participants: lottery.max_participants || '',
                status: lottery.status || 'active'
            });
        } else {
            setEditingLottery(null);
            setFormData({
                title: '',
                description: '',
                prize: '',
                start_date: '',
                end_date: '',
                max_participants: '',
                status: 'active'
            });
        }
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingLottery(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const token = localStorage.getItem('token');
            const url = editingLottery
                ? `${API_BASE_URL}/api/tenants/${tenantId}/lotteries/${editingLottery.id}`
                : `${API_BASE_URL}/api/tenants/${tenantId}/lotteries`;
            
            const method = editingLottery ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({
                    ...formData,
                    max_participants: formData.max_participants ? parseInt(formData.max_participants) : null
                })
            });

            if (response.ok) {
                await loadLotteries();
                closeModal();
                alert(editingLottery ? 'Lottery updated!' : 'Lottery created!');
            } else {
                const error = await response.json();
                alert(`Failed: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to save lottery:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this lottery?')) return;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/lotteries/${id}`, {
                method: 'DELETE',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                await loadLotteries();
                alert('Lottery deleted!');
            }
        } catch (error) {
            console.error('Failed to delete lottery:', error);
        }
    };

    const drawWinner = async (lotteryId) => {
        if (!confirm('Are you sure you want to draw a winner? This action cannot be undone.')) return;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/lotteries/${lotteryId}/draw`, {
                method: 'POST',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                const winner = await response.json();
                setSelectedWinner(winner);
                setShowWinnerModal(true);
                await loadLotteries();
            } else {
                alert('Failed to draw winner');
            }
        } catch (error) {
            console.error('Failed to draw winner:', error);
            // Mock winner for demo
            setSelectedWinner({
                name: 'John Doe',
                phone: '+971501234567',
                email: 'john@example.com'
            });
            setShowWinnerModal(true);
        }
    };

    const toggleStatus = async (lotteryId, currentStatus) => {
        const newStatus = currentStatus === 'active' ? 'paused' : 'active';
        
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/lotteries/${lotteryId}/status`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                await loadLotteries();
            }
        } catch (error) {
            console.error('Failed to toggle status:', error);
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <Gift className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Lottery & Giveaways</h2>
                        <p className="text-gray-400 text-sm">Create campaigns to engage leads</p>
                    </div>
                </div>
                <button
                    onClick={() => openModal()}
                    className="flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                    <Plus size={20} />
                    New Lottery
                </button>
            </div>

            {/* Lotteries List */}
            {lotteries.length === 0 ? (
                <div className="glass-card rounded-xl p-12 text-center">
                    <Gift className="text-gray-600 mx-auto mb-4" size={64} />
                    <h3 className="text-white text-xl font-semibold mb-2">No Lotteries Yet</h3>
                    <p className="text-gray-400 mb-6">Create your first lottery campaign to engage your leads</p>
                    <button
                        onClick={() => openModal()}
                        className="bg-gold-500 hover:bg-gold-400 text-navy-900 px-6 py-3 rounded-lg font-semibold"
                    >
                        Create Lottery
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {lotteries.map(lottery => (
                        <div key={lottery.id} className="glass-card rounded-xl p-6 space-y-4">
                            {/* Header */}
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                        <h3 className="text-white font-semibold text-lg">{lottery.title}</h3>
                                        <span className={`text-xs px-2 py-1 rounded-full ${
                                            lottery.status === 'active' ? 'bg-green-500/20 text-green-400' :
                                            lottery.status === 'completed' ? 'bg-blue-500/20 text-blue-400' :
                                            'bg-gray-500/20 text-gray-400'
                                        }`}>
                                            {lottery.status}
                                        </span>
                                    </div>
                                    <p className="text-gray-400 text-sm">{lottery.description}</p>
                                </div>
                                <Gift className="text-gold-500" size={24} />
                            </div>

                            {/* Prize */}
                            <div className="bg-gold-500/10 border border-gold-500/30 rounded-lg p-3">
                                <p className="text-gold-500 font-semibold">🏆 Prize: {lottery.prize}</p>
                            </div>

                            {/* Stats */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="bg-navy-800 rounded-lg p-3">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Users size={16} className="text-gray-400" />
                                        <span className="text-gray-400 text-xs">Participants</span>
                                    </div>
                                    <p className="text-white font-semibold">
                                        {lottery.participants || 0} / {lottery.max_participants || '∞'}
                                    </p>
                                </div>
                                <div className="bg-navy-800 rounded-lg p-3">
                                    <div className="flex items-center gap-2 mb-1">
                                        <Calendar size={16} className="text-gray-400" />
                                        <span className="text-gray-400 text-xs">Duration</span>
                                    </div>
                                    <p className="text-white font-semibold text-sm">
                                        {new Date(lottery.start_date).toLocaleDateString()} - {new Date(lottery.end_date).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>

                            {/* Winner Display */}
                            {lottery.winner && (
                                <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                                    <div className="flex items-center gap-2">
                                        <Trophy className="text-green-400" size={16} />
                                        <div>
                                            <p className="text-green-400 text-xs">Winner:</p>
                                            <p className="text-white font-semibold">{lottery.winner.name}</p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2 pt-2 border-t border-white/10">
                                {lottery.status === 'active' && !lottery.winner && (
                                    <>
                                        <button
                                            onClick={() => drawWinner(lottery.id)}
                                            className="flex-1 flex items-center justify-center gap-2 bg-green-500 hover:bg-green-400 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                                        >
                                            <Trophy size={16} />
                                            Draw Winner
                                        </button>
                                        <button
                                            onClick={() => toggleStatus(lottery.id, lottery.status)}
                                            className="flex items-center justify-center bg-yellow-500/20 hover:bg-yellow-500/30 text-yellow-400 px-3 py-2 rounded-lg transition-colors"
                                            title="Pause"
                                        >
                                            <Pause size={16} />
                                        </button>
                                    </>
                                )}
                                {lottery.status === 'paused' && (
                                    <button
                                        onClick={() => toggleStatus(lottery.id, lottery.status)}
                                        className="flex-1 flex items-center justify-center gap-2 bg-green-500/20 hover:bg-green-500/30 text-green-400 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                                    >
                                        <Play size={16} />
                                        Resume
                                    </button>
                                )}
                                <button
                                    onClick={() => openModal(lottery)}
                                    className="flex items-center justify-center bg-navy-800 hover:bg-navy-700 text-white px-3 py-2 rounded-lg transition-colors"
                                    title="Edit"
                                >
                                    <Edit size={16} />
                                </button>
                                <button
                                    onClick={() => handleDelete(lottery.id)}
                                    className="flex items-center justify-center bg-red-500/20 hover:bg-red-500/30 text-red-400 px-3 py-2 rounded-lg transition-colors"
                                    title="Delete"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Create/Edit Modal */}
            {showModal && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-2 sm:p-4">
                    <div className="bg-navy-900 rounded-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <h3 className="text-white text-xl font-semibold">
                                {editingLottery ? 'Edit Lottery' : 'Create Lottery'}
                            </h3>
                            <button onClick={closeModal} className="text-gray-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-4">
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="text-gray-400 text-sm block mb-2">Campaign Title</label>
                                    <input
                                        type="text"
                                        value={formData.title}
                                        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                        placeholder="e.g., Summer Villa Giveaway"
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                        required
                                    />
                                </div>

                                <div className="col-span-2">
                                    <label className="text-gray-400 text-sm block mb-2">Description</label>
                                    <textarea
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        placeholder="Describe the lottery..."
                                        rows={3}
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none resize-none"
                                    />
                                </div>

                                <div className="col-span-2">
                                    <label className="text-gray-400 text-sm block mb-2">Prize</label>
                                    <input
                                        type="text"
                                        value={formData.prize}
                                        onChange={(e) => setFormData({ ...formData, prize: e.target.value })}
                                        placeholder="e.g., Luxury Villa worth $2M"
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="text-gray-400 text-sm block mb-2">Start Date</label>
                                    <input
                                        type="date"
                                        value={formData.start_date}
                                        onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                        required
                                    />
                                </div>

                                <div>
                                    <label className="text-gray-400 text-sm block mb-2">End Date</label>
                                    <input
                                        type="date"
                                        value={formData.end_date}
                                        onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                        required
                                    />
                                </div>

                                <div className="col-span-2">
                                    <label className="text-gray-400 text-sm block mb-2">Max Participants (optional)</label>
                                    <input
                                        type="number"
                                        value={formData.max_participants}
                                        onChange={(e) => setFormData({ ...formData, max_participants: e.target.value })}
                                        placeholder="Leave empty for unlimited"
                                        className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                    />
                                </div>
                            </div>

                            <div className="flex gap-3 pt-4 border-t border-white/10">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="flex-1 px-4 py-3 rounded-lg border border-white/10 text-white hover:bg-white/5 transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 px-4 py-3 rounded-lg bg-gold-500 text-navy-900 font-semibold hover:bg-gold-400 transition-colors"
                                >
                                    {editingLottery ? 'Update Lottery' : 'Create Lottery'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Winner Announcement Modal */}
            {showWinnerModal && selectedWinner && (
                <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
                    <div className="bg-navy-900 rounded-xl w-full max-w-md text-center p-8">
                        <div className="mb-6">
                            <div className="w-20 h-20 bg-gold-500 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Trophy className="text-navy-900" size={40} />
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">🎉 We Have a Winner!</h2>
                            <p className="text-gray-400">Congratulations to:</p>
                        </div>

                        <div className="bg-gold-500/10 border border-gold-500/30 rounded-lg p-6 mb-6">
                            <p className="text-gold-500 text-2xl font-bold mb-2">{selectedWinner.name}</p>
                            <p className="text-white">{selectedWinner.phone}</p>
                            {selectedWinner.email && (
                                <p className="text-gray-400 text-sm mt-1">{selectedWinner.email}</p>
                            )}
                        </div>

                        <button
                            onClick={() => setShowWinnerModal(false)}
                            className="w-full bg-gold-500 hover:bg-gold-400 text-navy-900 font-semibold py-3 rounded-lg transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Lottery;
