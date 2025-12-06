/**
 * Simple PDF Upload for Lazy Agents 😎
 * Just upload PDF → AI extracts everything → Property created!
 */

import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader } from 'lucide-react';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

const PDFPropertyUpload = ({ tenantId, onPropertyCreated }) => {
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Step 1: Upload PDF and extract data
            const uploadResponse = await fetch(
                `${API_BASE_URL}/api/tenants/${tenantId}/properties/upload-pdf?extract_text=true`,
                {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                }
            );

            if (!uploadResponse.ok) {
                throw new Error('Failed to upload PDF');
            }

            const uploadData = await uploadResponse.json();
            
            // Step 2: Auto-create property with extracted data
            const propertyData = {
                name: uploadData.extracted_data?.name || file.name.replace('.pdf', ''),
                property_type: 'APARTMENT', // Default
                transaction_type: 'BUY',
                location: uploadData.extracted_data?.location || '',
                price: uploadData.extracted_data?.price || null,
                bedrooms: uploadData.extracted_data?.bedrooms || null,
                area_sqft: uploadData.extracted_data?.area_sqft || null,
                brochure_pdf: uploadData.file_url,
                description: uploadData.extracted_data?.description || '',
                is_available: true
            };

            const createResponse = await fetch(
                `${API_BASE_URL}/api/tenants/${tenantId}/properties`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    },
                    body: JSON.stringify(propertyData)
                }
            );

            if (!createResponse.ok) {
                throw new Error('Failed to create property');
            }

            const createdProperty = await createResponse.json();

            setResult({
                success: true,
                property: createdProperty,
                extracted: uploadData.extracted_data
            });

            if (onPropertyCreated) {
                onPropertyCreated(createdProperty);
            }

        } catch (err) {
            console.error('Upload error:', err);
            setError(err.message);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="glass-card rounded-2xl p-8 max-w-2xl mx-auto">
            <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gold-500 bg-opacity-20 rounded-full mb-4">
                    <FileText className="w-8 h-8 text-gold-500" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-2">
                    📄 Quick Property Upload
                </h2>
                <p className="text-gray-400">
                    برای ایجنت های تنبل 😎 فقط PDF بذار، بقیه‌ش با ما!
                </p>
            </div>

            {/* Upload Area */}
            {!result && !uploading && (
                <div className="relative">
                    <input
                        type="file"
                        accept=".pdf"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="pdf-upload"
                    />
                    <label
                        htmlFor="pdf-upload"
                        className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed border-gold-500 border-opacity-30 rounded-xl cursor-pointer hover:border-opacity-60 transition-all bg-navy-light hover:bg-opacity-80"
                    >
                        <Upload className="w-12 h-12 text-gold-500 mb-4" />
                        <p className="text-lg font-semibold text-white mb-2">
                            Click to upload PDF brochure
                        </p>
                        <p className="text-sm text-gray-400">
                            Max 10MB • We'll extract all property details automatically
                        </p>
                    </label>
                </div>
            )}

            {/* Uploading State */}
            {uploading && (
                <div className="flex flex-col items-center justify-center py-12">
                    <Loader className="w-12 h-12 text-gold-500 animate-spin mb-4" />
                    <p className="text-white font-semibold">Uploading and extracting data...</p>
                    <p className="text-gray-400 text-sm mt-2">This may take a few seconds</p>
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="flex items-start gap-3 bg-red-500 bg-opacity-10 border border-red-500 rounded-lg p-4 mb-4">
                    <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                    <div>
                        <p className="text-red-500 font-semibold">Upload Failed</p>
                        <p className="text-red-400 text-sm">{error}</p>
                        <button
                            onClick={() => setError(null)}
                            className="text-red-400 text-sm underline mt-2"
                        >
                            Try again
                        </button>
                    </div>
                </div>
            )}

            {/* Success State */}
            {result && result.success && (
                <div className="space-y-4">
                    <div className="flex items-start gap-3 bg-green-500 bg-opacity-10 border border-green-500 rounded-lg p-4">
                        <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                        <div className="flex-1">
                            <p className="text-green-500 font-semibold">✅ Property Created Successfully!</p>
                            <p className="text-green-400 text-sm">PDF uploaded and data extracted</p>
                        </div>
                    </div>

                    {/* Extracted Data Preview */}
                    <div className="glass-card rounded-lg p-4">
                        <h3 className="text-white font-semibold mb-3">Extracted Information:</h3>
                        <div className="grid grid-cols-2 gap-3 text-sm">
                            {result.extracted?.price && (
                                <div>
                                    <span className="text-gray-400">Price:</span>
                                    <span className="text-white ml-2">{result.extracted.price.toLocaleString()} AED</span>
                                </div>
                            )}
                            {result.extracted?.bedrooms && (
                                <div>
                                    <span className="text-gray-400">Bedrooms:</span>
                                    <span className="text-white ml-2">{result.extracted.bedrooms}</span>
                                </div>
                            )}
                            {result.extracted?.area_sqft && (
                                <div>
                                    <span className="text-gray-400">Area:</span>
                                    <span className="text-white ml-2">{result.extracted.area_sqft} sqft</span>
                                </div>
                            )}
                            {result.extracted?.location && (
                                <div>
                                    <span className="text-gray-400">Location:</span>
                                    <span className="text-white ml-2">{result.extracted.location}</span>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button
                            onClick={() => setResult(null)}
                            className="flex-1 bg-gold-500 text-navy-900 font-semibold py-3 rounded-lg hover:bg-gold-400 transition-all"
                        >
                            Upload Another PDF
                        </button>
                        <button
                            onClick={() => window.location.href = '/properties'}
                            className="flex-1 bg-navy-light text-white font-semibold py-3 rounded-lg hover:bg-opacity-80 transition-all"
                        >
                            View All Properties
                        </button>
                    </div>
                </div>
            )}

            {/* How it Works */}
            <div className="mt-8 pt-6 border-t border-white border-opacity-10">
                <h3 className="text-white font-semibold mb-3 text-center">چطور کار می‌کنه؟</h3>
                <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                        <div className="w-10 h-10 bg-gold-500 bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-gold-500 font-bold">1</span>
                        </div>
                        <p className="text-sm text-gray-400">Upload PDF</p>
                    </div>
                    <div>
                        <div className="w-10 h-10 bg-gold-500 bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-gold-500 font-bold">2</span>
                        </div>
                        <p className="text-sm text-gray-400">AI Extracts Data</p>
                    </div>
                    <div>
                        <div className="w-10 h-10 bg-gold-500 bg-opacity-20 rounded-full flex items-center justify-center mx-auto mb-2">
                            <span className="text-gold-500 font-bold">3</span>
                        </div>
                        <p className="text-sm text-gray-400">Property Created!</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PDFPropertyUpload;
