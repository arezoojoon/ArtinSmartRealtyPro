/**
 * Artin Smart Realty V2 - Properties Management Component
 * Manage tenant's property inventory
 */

import React, { useState, useEffect } from 'react';
import {
    Building2,
    Plus,
    Edit,
    Trash2,
    X,
    Home,
    DollarSign,
    MapPin,
    Bed,
    Bath,
    Square,
    TrendingUp,
    Award,
    Save,
    AlertCircle,
    FileText,
    Upload,
    Sparkles
} from 'lucide-react';
import PropertyImageUpload from './PropertyImageUpload';
import PDFPropertyUpload from './PDFPropertyUpload';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const getAuthHeaders = () => {
    const token = localStorage.getItem('token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
};

const PROPERTY_TYPES = [
    { value: 'APARTMENT', label: 'Apartment' },
    { value: 'VILLA', label: 'Villa' },
    { value: 'PENTHOUSE', label: 'Penthouse' },
    { value: 'TOWNHOUSE', label: 'Townhouse' },
    { value: 'STUDIO', label: 'Studio' },
    { value: 'COMMERCIAL', label: 'Commercial' },
    { value: 'LAND', label: 'Land' },
];

const TRANSACTION_TYPES = [
    { value: 'BUY', label: 'Buy' },
    { value: 'RENT', label: 'Rent' },
];

const PropertiesManagement = ({ tenantId }) => {
    const [properties, setProperties] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [showPDFUpload, setShowPDFUpload] = useState(false);
    const [editingProperty, setEditingProperty] = useState(null);
    const [formData, setFormData] = useState({
        name: '',
        property_type: 'apartment',  // Lowercase to match API enum values
        transaction_type: 'buy',     // Lowercase to match API enum values
        location: '',
        address: '',
        price: '',
        price_per_sqft: '',
        currency: 'AED',
        bedrooms: '',
        bathrooms: '',
        area_sqft: '',
        features: '',
        description: '',
        full_description: '',  // Rich text with emojis
        expected_roi: '',
        rental_yield: '',
        golden_visa_eligible: false,
        is_featured: false,
        is_urgent: false,  // Urgent Sale flag
        image_urls: [],  // Property images
        brochure_pdf: '',  // PDF brochure URL
    });

    useEffect(() => {
        loadProperties();
    }, [tenantId]);

    const loadProperties = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/properties`, {
                headers: getAuthHeaders(),
            });
            const data = await response.json();
            setProperties(data);
        } catch (error) {
            console.error('Failed to load properties:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        console.log('Form submitted!', formData);  // Debug log
        
        try {
            const payload = {
                ...formData,
                price: formData.price ? parseFloat(formData.price) : null,
                price_per_sqft: formData.price_per_sqft ? parseFloat(formData.price_per_sqft) : null,
                bedrooms: formData.bedrooms ? parseInt(formData.bedrooms) : null,
                bathrooms: formData.bathrooms ? parseInt(formData.bathrooms) : null,
                area_sqft: formData.area_sqft ? parseFloat(formData.area_sqft) : null,
                expected_roi: formData.expected_roi ? parseFloat(formData.expected_roi) : null,
                rental_yield: formData.rental_yield ? parseFloat(formData.rental_yield) : null,
                features: formData.features ? formData.features.split(',').map(f => f.trim()) : [],
            };

            const url = editingProperty
                ? `${API_BASE_URL}/api/tenants/${tenantId}/properties/${editingProperty.id}`
                : `${API_BASE_URL}/api/tenants/${tenantId}/properties`;
            
            const method = editingProperty ? 'PUT' : 'POST';

            console.log('Sending request:', { method, url, payload });  // Debug log

            const response = await fetch(url, {
                method,
                headers: {
                    'Content-Type': 'application/json',
                    ...getAuthHeaders(),
                },
                body: JSON.stringify(payload),
            });

            console.log('Response:', response.status, response.statusText);  // Debug log

            if (response.ok) {
                const result = await response.json();
                console.log('Success:', result);  // Debug log
                await loadProperties();
                closeModal();
                alert(editingProperty ? 'Property updated successfully!' : 'Property created successfully!');
            } else {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                console.error('Server error:', error);
                alert(`Failed to save property: ${error.detail || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Failed to save property:', error);
            alert(`Error: ${error.message}`);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure you want to delete this property?')) return;

        try {
            const response = await fetch(`${API_BASE_URL}/api/tenants/${tenantId}/properties/${id}`, {
                method: 'DELETE',
                headers: getAuthHeaders(),
            });

            if (response.ok) {
                await loadProperties();
            }
        } catch (error) {
            console.error('Failed to delete property:', error);
        }
    };

    const openModal = (property = null) => {
        console.log('Opening modal for property:', property);  // Debug log
        if (property) {
            setEditingProperty(property);
            setFormData({
                name: property.name || '',
                property_type: property.property_type?.toLowerCase() || 'apartment',  // Ensure lowercase
                transaction_type: property.transaction_type?.toLowerCase() || 'buy',  // Ensure lowercase
                location: property.location || '',
                address: property.address || '',
                price: property.price || '',
                price_per_sqft: property.price_per_sqft || '',
                currency: property.currency || 'AED',
                bedrooms: property.bedrooms || '',
                bathrooms: property.bathrooms || '',
                area_sqft: property.area_sqft || '',
                features: property.features?.join(', ') || '',
                description: property.description || '',
                full_description: property.full_description || '',
                expected_roi: property.expected_roi || '',
                rental_yield: property.rental_yield || '',
                golden_visa_eligible: property.golden_visa_eligible || false,
                is_featured: property.is_featured || false,
                is_urgent: property.is_urgent || false,
                image_urls: property.image_urls || [],
                brochure_pdf: property.brochure_pdf || '',
            });
        } else {
            setEditingProperty(null);
            setFormData({
                name: '',
                property_type: 'apartment',  // Lowercase to match API
                transaction_type: 'buy',     // Lowercase to match API
                location: '',
                address: '',
                price: '',
                price_per_sqft: '',
                currency: 'AED',
                bedrooms: '',
                bathrooms: '',
                area_sqft: '',
                features: '',
                description: '',
                full_description: '',
                expected_roi: '',
                rental_yield: '',
                golden_visa_eligible: false,
                is_featured: false,
                is_urgent: false,
                image_urls: [],
                brochure_pdf: '',
            });
        }
        console.log('Setting showModal to true');  // Debug log
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setEditingProperty(null);
    };

    const handleInputChange = (e) => {
        const { name, value, type, checked } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? checked : value
        }));
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold"></div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white">Properties</h2>
                    <p className="text-gray-400 mt-1">Manage your property inventory</p>
                </div>
                <div className="flex gap-3">
                    <button
                        onClick={() => setShowPDFUpload(true)}
                        className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white px-6 py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-purple-500/50 transition-all"
                    >
                        <Sparkles className="w-5 h-5" />
                        🚀 AI Smart Upload
                    </button>
                    <button
                        onClick={() => openModal()}
                        className="flex items-center gap-2 bg-gradient-to-r from-gold to-amber-600 text-navy px-6 py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-gold/50 transition-all"
                    >
                        <Plus className="w-5 h-5" />
                        Add Manual
                    </button>
                </div>
            </div>

            {/* Properties Grid */}
            {properties.length === 0 ? (
                <div className="glass-card p-12 text-center">
                    <Building2 className="w-16 h-16 text-gray-500 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-gray-400 mb-2">No Properties Yet</h3>
                    <p className="text-gray-500 mb-6">Add your first property to get started</p>
                    <button
                        onClick={() => openModal()}
                        className="bg-gold text-navy px-6 py-2 rounded-lg font-semibold hover:shadow-lg transition-all inline-flex items-center gap-2"
                    >
                        <Plus className="w-4 h-4" />
                        Add Property
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {properties.map((property) => (
                        <div key={property.id} className="glass-card p-6 hover:shadow-xl transition-shadow">
                            {/* Featured Badge */}
                            {property.is_featured && (
                                <div className="flex justify-end mb-2">
                                    <span className="bg-gold text-navy text-xs font-bold px-2 py-1 rounded">
                                        FEATURED
                                    </span>
                                </div>
                            )}

                            {/* Property Name */}
                            <h3 className="text-lg font-bold text-white mb-2">{property.name}</h3>

                            {/* Location */}
                            <div className="flex items-center gap-2 text-gray-400 mb-4">
                                <MapPin className="w-4 h-4" />
                                <span className="text-sm">{property.location}</span>
                            </div>

                            {/* Type & Transaction */}
                            <div className="flex gap-2 mb-4">
                                <span className="bg-navy-light px-3 py-1 rounded text-xs text-gray-300">
                                    {property.property_type}
                                </span>
                                <span className="bg-navy-light px-3 py-1 rounded text-xs text-gray-300">
                                    {property.transaction_type}
                                </span>
                            </div>

                            {/* Price */}
                            {property.price && (
                                <div className="flex items-center gap-2 mb-4">
                                    <DollarSign className="w-5 h-5 text-gold" />
                                    <span className="text-xl font-bold text-gold">
                                        {property.currency} {property.price.toLocaleString()}
                                    </span>
                                </div>
                            )}

                            {/* Details */}
                            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-4 text-center">
                                {property.bedrooms !== null && (
                                    <div>
                                        <Bed className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                        <span className="text-sm text-gray-300">{property.bedrooms}</span>
                                    </div>
                                )}
                                {property.bathrooms !== null && (
                                    <div>
                                        <Bath className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                        <span className="text-sm text-gray-300">{property.bathrooms}</span>
                                    </div>
                                )}
                                {property.area_sqft && (
                                    <div>
                                        <Square className="w-4 h-4 text-gray-400 mx-auto mb-1" />
                                        <span className="text-sm text-gray-300">{property.area_sqft} sqft</span>
                                    </div>
                                )}
                            </div>

                            {/* ROI & Yield */}
                            {(property.expected_roi || property.rental_yield) && (
                                <div className="flex gap-4 mb-4">
                                    {property.expected_roi && (
                                        <div className="flex items-center gap-1 text-green-400 text-sm">
                                            <TrendingUp className="w-4 h-4" />
                                            <span>ROI {property.expected_roi}%</span>
                                        </div>
                                    )}
                                    {property.rental_yield && (
                                        <div className="flex items-center gap-1 text-blue-400 text-sm">
                                            <TrendingUp className="w-4 h-4" />
                                            <span>Yield {property.rental_yield}%</span>
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Golden Visa */}
                            {property.golden_visa_eligible && (
                                <div className="flex items-center gap-2 mb-4">
                                    <Award className="w-4 h-4 text-gold" />
                                    <span className="text-xs text-gold">Golden Visa Eligible</span>
                                </div>
                            )}

                            {/* Actions */}
                            <div className="flex gap-2 pt-4 border-t border-gray-700">
                                <button
                                    onClick={() => openModal(property)}
                                    className="flex-1 flex items-center justify-center gap-2 bg-navy-light text-white px-4 py-2 rounded hover:bg-opacity-80 transition-all"
                                >
                                    <Edit className="w-4 h-4" />
                                    Edit
                                </button>
                                <button
                                    onClick={() => handleDelete(property.id)}
                                    className="flex items-center justify-center gap-2 bg-red-500 bg-opacity-20 text-red-400 px-4 py-2 rounded hover:bg-opacity-30 transition-all"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Add/Edit Modal */}
            {showModal && (
                <div 
                    className="fixed inset-0 bg-black bg-opacity-75 flex items-start justify-center p-4 z-50 overflow-y-auto"
                    style={{ zIndex: 9999 }}
                    onClick={(e) => {
                        // Close modal if clicking the backdrop
                        if (e.target === e.currentTarget) {
                            closeModal();
                        }
                    }}
                >
                    <div className="glass-card max-w-2xl w-full p-4 sm:p-6 my-4 sm:my-8 max-h-[85vh] overflow-y-auto">
                        {/* Modal Header */}
                        <div className="flex justify-between items-center mb-6">
                            <h3 className="text-2xl font-bold text-white">
                                {editingProperty ? 'Edit Property' : 'Add New Property'}
                            </h3>
                            <button
                                onClick={closeModal}
                                type="button"
                                className="text-gray-400 hover:text-white transition-colors"
                            >
                                <X className="w-6 h-6" />
                            </button>
                        </div>

                        {/* Form */}
                        <form onSubmit={handleSubmit} className="space-y-4">
                            {/* Name */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Property Name *
                                </label>
                                <input
                                    type="text"
                                    name="name"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    required
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                />
                            </div>

                            {/* Type & Transaction */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Property Type *
                                    </label>
                                    <select
                                        name="property_type"
                                        value={formData.property_type}
                                        onChange={handleInputChange}
                                        required
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    >
                                        {PROPERTY_TYPES.map(type => (
                                            <option key={type.value} value={type.value}>{type.label}</option>
                                        ))}
                                    </select>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Transaction Type
                                    </label>
                                    <select
                                        name="transaction_type"
                                        value={formData.transaction_type}
                                        onChange={handleInputChange}
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    >
                                        {TRANSACTION_TYPES.map(type => (
                                            <option key={type.value} value={type.value}>{type.label}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* Location */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Location *
                                </label>
                                <input
                                    type="text"
                                    name="location"
                                    value={formData.location}
                                    onChange={handleInputChange}
                                    required
                                    placeholder="e.g., Dubai Marina"
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                />
                            </div>

                            {/* Address */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Full Address
                                </label>
                                <input
                                    type="text"
                                    name="address"
                                    value={formData.address}
                                    onChange={handleInputChange}
                                    placeholder="Optional full address"
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                />
                            </div>

                            {/* Price Details */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Price
                                    </label>
                                    <input
                                        type="number"
                                        name="price"
                                        value={formData.price}
                                        onChange={handleInputChange}
                                        placeholder="0"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Price per sqft
                                    </label>
                                    <input
                                        type="number"
                                        name="price_per_sqft"
                                        value={formData.price_per_sqft}
                                        onChange={handleInputChange}
                                        placeholder="0"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>
                            </div>

                            {/* Bedrooms, Bathrooms, Area */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Bedrooms
                                    </label>
                                    <input
                                        type="number"
                                        name="bedrooms"
                                        value={formData.bedrooms}
                                        onChange={handleInputChange}
                                        placeholder="0"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Bathrooms
                                    </label>
                                    <input
                                        type="number"
                                        name="bathrooms"
                                        value={formData.bathrooms}
                                        onChange={handleInputChange}
                                        placeholder="0"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Area (sqft)
                                    </label>
                                    <input
                                        type="number"
                                        name="area_sqft"
                                        value={formData.area_sqft}
                                        onChange={handleInputChange}
                                        placeholder="0"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>
                            </div>

                            {/* Features */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Features (comma-separated)
                                </label>
                                <input
                                    type="text"
                                    name="features"
                                    value={formData.features}
                                    onChange={handleInputChange}
                                    placeholder="Sea View, Parking, Gym, Pool"
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Description
                                </label>
                                <textarea
                                    name="description"
                                    value={formData.description}
                                    onChange={handleInputChange}
                                    rows="3"
                                    placeholder="Property description..."
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                />
                            </div>

                            {/* Full Description (Rich Text with Emojis) */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Full Description (با ایموجی)
                                </label>
                                <textarea
                                    name="full_description"
                                    value={formData.full_description}
                                    onChange={handleInputChange}
                                    rows="8"
                                    placeholder="🏠 ویلا مدرن در شمال تهران&#10;📍 محدوده: سعادت آباد&#10;📏 متراژ: 250 متر&#10;🛏️ 3 خوابه + 3 سرویس&#10;✨ امکانات: پارکینگ، انباری، آسانسور..."
                                    className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold font-medium"
                                    style={{ direction: 'rtl', textAlign: 'right' }}
                                />
                            </div>

                            {/* Urgent Sale Flag */}
                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    name="is_urgent"
                                    checked={formData.is_urgent}
                                    onChange={(e) => setFormData({ ...formData, is_urgent: e.target.checked })}
                                    className="w-4 h-4 text-gold bg-navy-light border-gray-700 rounded focus:ring-gold focus:ring-2"
                                />
                                <label className="ml-2 text-sm font-medium text-gray-300">
                                    🔥 فروش فوری (Urgent Sale)
                                </label>
                            </div>

                            {/* Property Images */}
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Property Images (حداکثر 5 عکس)
                                </label>
                                {editingProperty?.id ? (
                                    <PropertyImageUpload
                                        propertyId={editingProperty.id}
                                        tenantId={tenantId}
                                        images={formData.image_urls || []}
                                        onImagesChange={(newImages) => {
                                            setFormData({ 
                                                ...formData, 
                                                image_urls: newImages 
                                            });
                                        }}
                                    />
                                ) : (
                                    <div className="bg-navy-light border border-gray-700 rounded-lg p-6 text-center text-gray-400">
                                        <p>💾 ابتدا ملک را ذخیره کنید، سپس می‌توانید عکس آپلود کنید</p>
                                    </div>
                                )}
                            </div>

                            {/* Property PDF Upload */}
                            {editingProperty?.id && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        📄 Property Brochure PDF (Auto-Fill)
                                    </label>
                                    <div className="space-y-3">
                                        <input
                                            type="file"
                                            accept=".pdf"
                                            onChange={async (e) => {
                                                const file = e.target.files[0];
                                                if (!file) return;

                                                const uploadFormData = new FormData();
                                                uploadFormData.append('file', file);

                                                try {
                                                    const response = await fetch(
                                                        `${API_BASE_URL}/api/tenants/${tenantId}/properties/upload-pdf?extract_text=true`,
                                                        {
                                                            method: 'POST',
                                                            body: uploadFormData,
                                                            headers: {
                                                                'Authorization': `Bearer ${localStorage.getItem('token')}`
                                                            }
                                                        }
                                                    );

                                                    if (!response.ok) throw new Error('Upload failed');

                                                    const data = await response.json();
                                                    
                                                    // Auto-fill form with extracted data
                                                    if (data.extracted_data) {
                                                        const extracted = data.extracted_data;
                                                        setFormData(prev => ({
                                                            ...prev,
                                                            price: extracted.price || prev.price,
                                                            bedrooms: extracted.bedrooms || prev.bedrooms,
                                                            area_sqft: extracted.area_sqft || prev.area_sqft,
                                                            location: extracted.location || prev.location,
                                                            brochure_pdf: data.file_url
                                                        }));
                                                        alert('✅ PDF uploaded and data extracted successfully!');
                                                    } else {
                                                        setFormData(prev => ({ ...prev, brochure_pdf: data.file_url }));
                                                        alert('✅ PDF uploaded successfully!');
                                                    }
                                                } catch (error) {
                                                    console.error('PDF upload error:', error);
                                                    alert('❌ Failed to upload PDF. Please try again.');
                                                }
                                            }}
                                            className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-gold file:text-navy file:font-semibold hover:file:bg-amber-500 cursor-pointer"
                                        />
                                        {formData.brochure_pdf && (
                                            <div className="flex items-center gap-2 bg-green-500 bg-opacity-10 border border-green-500 rounded-lg px-4 py-2">
                                                <FileText className="w-4 h-4 text-green-500" />
                                                <span className="text-sm text-green-500">PDF uploaded successfully</span>
                                            </div>
                                        )}
                                        <p className="text-xs text-gray-400">
                                            💡 Upload a property brochure PDF to auto-fill price, bedrooms, area, and location
                                        </p>
                                    </div>
                                </div>
                            )}
                            {!editingProperty?.id && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        📄 Property Brochure PDF
                                    </label>
                                    <div className="bg-navy-light border border-gray-700 rounded-lg p-6 text-center text-gray-400">
                                        <p>💾 ابتدا ملک را ذخیره کنید، سپس می‌توانید PDF آپلود کنید</p>
                                    </div>
                                </div>
                            )}

                            {/* ROI & Rental Yield */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Expected ROI (%)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        name="expected_roi"
                                        value={formData.expected_roi}
                                        onChange={handleInputChange}
                                        placeholder="8.5"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-2">
                                        Rental Yield (%)
                                    </label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        name="rental_yield"
                                        value={formData.rental_yield}
                                        onChange={handleInputChange}
                                        placeholder="7.2"
                                        className="w-full bg-navy-light border border-gray-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-gold"
                                    />
                                </div>
                            </div>

                            {/* Checkboxes */}
                            <div className="flex gap-6">
                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="golden_visa_eligible"
                                        checked={formData.golden_visa_eligible}
                                        onChange={handleInputChange}
                                        className="w-4 h-4 rounded border-gray-700 text-gold focus:ring-gold"
                                    />
                                    <span className="text-sm text-gray-300">Golden Visa Eligible</span>
                                </label>

                                <label className="flex items-center gap-2 cursor-pointer">
                                    <input
                                        type="checkbox"
                                        name="is_featured"
                                        checked={formData.is_featured}
                                        onChange={handleInputChange}
                                        className="w-4 h-4 rounded border-gray-700 text-gold focus:ring-gold"
                                    />
                                    <span className="text-sm text-gray-300">Featured Property</span>
                                </label>
                            </div>

                            {/* Actions */}
                            <div className="flex gap-4 pt-4">
                                <button
                                    type="button"
                                    onClick={closeModal}
                                    className="flex-1 bg-gray-700 text-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-600 transition-all"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="flex-1 bg-gradient-to-r from-gold to-amber-600 text-navy px-6 py-3 rounded-lg font-semibold hover:shadow-lg hover:shadow-gold/50 transition-all flex items-center justify-center gap-2"
                                >
                                    <Save className="w-5 h-5" />
                                    {editingProperty ? 'Update' : 'Create'} Property
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* PDF Quick Upload Modal - AI-Powered Vision Analysis */}
            {showPDFUpload && (
                <PDFPropertyUpload
                    tenantId={tenantId}
                    onPropertyCreated={() => {
                        loadProperties();  // Refresh property list
                    }}
                    onClose={() => {
                        setShowPDFUpload(false);
                        loadProperties();  // Refresh in case properties were auto-saved
                    }}
                />
            )}
        </div>
    );
};

export default PropertiesManagement;
