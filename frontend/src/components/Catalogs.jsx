/**
 * Artin Smart Realty V2 - Property Catalogs
 * Create and manage property catalogs/portfolios
 */

import React, { useState, useEffect } from 'react';
import { BookOpen, Plus, Edit, Trash2, Eye, Download, Share2, X } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const Catalogs = ({ tenantId }) => {
    const [catalogs, setCatalogs] = useState([]);
    const [properties, setProperties] = useState([]);
    const [showModal, setShowModal] = useState(false);
    const [editingCatalog, setEditingCatalog] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        property_ids: []
    });

    useEffect(() => {
        loadCatalogs();
        loadProperties();
    }, [tenantId]);

    const loadCatalogs = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/catalogs`, {
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });
            if (response.ok) {
                const data = await response.json();
                setCatalogs(data);
            }
        } catch (error) {
            console.error('Failed to load catalogs:', error);
        }
    };

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

    const openModal = (catalog = null) => {
        if (catalog) {
            setEditingCatalog(catalog);
            setFormData({
                name: catalog.name || '',
                description: catalog.description || '',
                property_ids: catalog.property_ids || []
            });
        } else {
            setEditingCatalog(null);
            setFormData({
                name: '',
                description: '',
                property_ids: []
            });
        }
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingCatalog(null);
        setFormData({ name: '', description: '', property_ids: [] });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        try {
            const token = localStorage.getItem('token');
            const url = editingCatalog
                ? `${API_BASE_URL}/api/tenants/${tenantId}/catalogs/${editingCatalog.id}`
                : `${API_BASE_URL}/api/tenants/${tenantId}/catalogs`;
            
            const method = editingCatalog ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                await loadCatalogs();
                closeModal();
                alert(editingCatalog ? 'Catalog updated!' : 'Catalog created!');
            } else {
                const error = await response.json();
                alert(`Failed: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to save catalog:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this catalog?')) return;

        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/catalogs/${id}`, {
                method: 'DELETE',
                headers: token ? { 'Authorization': `Bearer ${token}` } : {}
            });

            if (response.ok) {
                await loadCatalogs();
                alert('Catalog deleted!');
            }
        } catch (error) {
            console.error('Failed to delete catalog:', error);
        }
    };

    const toggleProperty = (propertyId) => {
        if (formData.property_ids.includes(propertyId)) {
            setFormData({
                ...formData,
                property_ids: formData.property_ids.filter(id => id !== propertyId)
            });
        } else {
            setFormData({
                ...formData,
                property_ids: [...formData.property_ids, propertyId]
            });
        }
    };

    const downloadCatalog = (catalogId) => {
        window.open(`${API_BASE_URL}/api/tenants/${tenantId}/catalogs/${catalogId}/download`, '_blank');
    };

    const shareCatalog = (catalogId) => {
        const shareUrl = `${window.location.origin}/catalog/${catalogId}`;
        navigator.clipboard.writeText(shareUrl);
        alert('Catalog link copied to clipboard!');
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-navy-800 rounded-lg">
                        <BookOpen className="text-gold-500" size={24} />
                    </div>
                    <div>
                        <h2 className="text-xl font-semibold text-white">Property Catalogs</h2>
                        <p className="text-gray-400 text-sm">Create portfolios and brochures</p>
                    </div>
                </div>
                <button
                    onClick={() => openModal()}
                    className="flex items-center gap-2 bg-gold-500 hover:bg-gold-400 text-navy-900 px-4 py-2 rounded-lg font-semibold transition-colors"
                >
                    <Plus size={20} />
                    New Catalog
                </button>
            </div>

            {/* Catalogs Grid */}
            {catalogs.length === 0 ? (
                <div className="glass-card rounded-xl p-12 text-center">
                    <BookOpen className="text-gray-600 mx-auto mb-4" size={64} />
                    <h3 className="text-white text-xl font-semibold mb-2">No Catalogs Yet</h3>
                    <p className="text-gray-400 mb-6">Create your first property catalog to showcase your listings</p>
                    <button
                        onClick={() => openModal()}
                        className="bg-gold-500 hover:bg-gold-400 text-navy-900 px-6 py-3 rounded-lg font-semibold"
                    >
                        Create Catalog
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {catalogs.map(catalog => (
                        <div key={catalog.id} className="glass-card rounded-xl p-6 space-y-4">
                            {/* Catalog Header */}
                            <div className="flex items-start justify-between">
                                <div className="flex-1">
                                    <h3 className="text-white font-semibold text-lg mb-1">{catalog.name}</h3>
                                    <p className="text-gray-400 text-sm line-clamp-2">{catalog.description}</p>
                                </div>
                                <BookOpen className="text-gold-500" size={24} />
                            </div>

                            {/* Stats */}
                            <div className="flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-1">
                                    <span className="text-gray-400">Properties:</span>
                                    <span className="text-white font-semibold">{catalog.property_ids?.length || 0}</span>
                                </div>
                                <div className="flex items-center gap-1">
                                    <span className="text-gray-400">Views:</span>
                                    <span className="text-white font-semibold">{catalog.views || 0}</span>
                                </div>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-2">
                                <button
                                    onClick={() => downloadCatalog(catalog.id)}
                                    className="flex-1 flex items-center justify-center gap-2 bg-green-500 hover:bg-green-400 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                                    title="Download PDF"
                                >
                                    <Download size={16} />
                                    PDF
                                </button>
                                <button
                                    onClick={() => shareCatalog(catalog.id)}
                                    className="flex-1 flex items-center justify-center gap-2 bg-blue-500 hover:bg-blue-400 text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                                    title="Share Link"
                                >
                                    <Share2 size={16} />
                                    Share
                                </button>
                                <button
                                    onClick={() => openModal(catalog)}
                                    className="flex items-center justify-center bg-navy-800 hover:bg-navy-700 text-white p-2 rounded-lg transition-colors"
                                    title="Edit"
                                >
                                    <Edit size={16} />
                                </button>
                                <button
                                    onClick={() => handleDelete(catalog.id)}
                                    className="flex items-center justify-center bg-red-500/20 hover:bg-red-500/30 text-red-400 p-2 rounded-lg transition-colors"
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
                    <div className="bg-navy-900 rounded-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
                        {/* Modal Header */}
                        <div className="flex items-center justify-between p-6 border-b border-white/10">
                            <h3 className="text-white text-xl font-semibold">
                                {editingCatalog ? 'Edit Catalog' : 'Create Catalog'}
                            </h3>
                            <button onClick={closeModal} className="text-gray-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="p-6 space-y-6">
                            {/* Catalog Name */}
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Catalog Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="e.g., Luxury Villas Collection"
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none"
                                    required
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">Description</label>
                                <textarea
                                    value={formData.description}
                                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                    placeholder="Describe this catalog..."
                                    rows={3}
                                    className="w-full bg-navy-800 text-white rounded-lg px-4 py-3 border border-white/10 outline-none resize-none"
                                />
                            </div>

                            {/* Property Selection */}
                            <div>
                                <label className="text-gray-400 text-sm block mb-2">
                                    Select Properties ({formData.property_ids.length} selected)
                                </label>
                                <div className="bg-navy-800 rounded-lg border border-white/10 p-4 max-h-64 overflow-y-auto space-y-2">
                                    {properties.length === 0 ? (
                                        <p className="text-gray-500 text-sm text-center py-4">No properties available</p>
                                    ) : (
                                        properties.map(property => (
                                            <label
                                                key={property.id}
                                                className="flex items-center gap-3 p-3 bg-navy-900 rounded-lg cursor-pointer hover:bg-navy-800 transition-colors"
                                            >
                                                <input
                                                    type="checkbox"
                                                    checked={formData.property_ids.includes(property.id)}
                                                    onChange={() => toggleProperty(property.id)}
                                                    className="w-4 h-4 rounded border-gray-600 text-gold-500 focus:ring-gold-500"
                                                />
                                                <div className="flex-1">
                                                    <p className="text-white text-sm font-medium">{property.name}</p>
                                                    <p className="text-gray-400 text-xs">{property.location}</p>
                                                </div>
                                                <span className="text-gold-500 text-sm font-semibold">
                                                    {property.price} {property.currency}
                                                </span>
                                            </label>
                                        ))
                                    )}
                                </div>
                            </div>

                            {/* Action Buttons */}
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
                                    {editingCatalog ? 'Update Catalog' : 'Create Catalog'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Catalogs;
