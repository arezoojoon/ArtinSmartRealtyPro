/**
 * Property Image Upload Component
 * Drag-and-drop multiple image upload with preview
 */

import React, { useState, useCallback, useEffect } from 'react';
import { Upload, X, Image as ImageIcon, Trash2, Star } from 'lucide-react';

const MAX_IMAGES = 5;
const MAX_FILE_SIZE = 3 * 1024 * 1024; // 3MB - محدودیت حجم برای بهینه‌سازی

const PropertyImageUpload = ({ propertyId, tenantId, images = [], onImagesChange }) => {
    const [uploading, setUploading] = useState(false);
    const [dragActive, setDragActive] = useState(false);
    const [previewImages, setPreviewImages] = useState(images);

    // اصلاح: sync با images prop
    useEffect(() => {
        setPreviewImages(images);
    }, [images]);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('token');
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    };

    const handleDrag = useCallback((e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    }, []);

    const validateFile = (file) => {
        // بررسی نوع فایل - فقط عکس
        if (!file.type.startsWith('image/')) {
            return '❌ فقط فایل‌های تصویری (عکس) مجاز هستند';
        }
        
        // بررسی فرمت عکس - فقط JPG, PNG, WebP
        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!allowedTypes.includes(file.type)) {
            return '❌ فقط فرمت‌های JPG، PNG و WebP مجاز هستند';
        }
        
        // بررسی حجم فایل - حداکثر 3MB
        const fileSizeMB = file.size / 1024 / 1024;
        if (file.size > MAX_FILE_SIZE) {
            return `❌ حجم فایل (${fileSizeMB.toFixed(2)}MB) بیش از حد مجاز است! حداکثر ${MAX_FILE_SIZE / 1024 / 1024}MB`;
        }
        
        return null;
    };

    const uploadImages = async (files) => {
        if (!propertyId || !tenantId) {
            alert('⚠️ ابتدا باید ملک را ذخیره کنید، سپس می‌توانید عکس آپلود کنید');
            return;
        }

        // بررسی تعداد کل عکس‌ها
        const totalImages = previewImages.length + files.length;
        if (totalImages > MAX_IMAGES) {
            alert(
                `❌ تعداد عکس‌ها بیش از حد مجاز است!\n\n` +
                `حداکثر: ${MAX_IMAGES} عکس\n` +
                `موجود: ${previewImages.length} عکس\n` +
                `انتخاب شده: ${files.length} عکس\n` +
                `جمع: ${totalImages} عکس\n\n` +
                `لطفاً تعداد کمتری عکس انتخاب کنید.`
            );
            return;
        }

        // بررسی تعداد فایل‌های انتخابی
        if (files.length === 0) {
            alert('⚠️ هیچ فایلی انتخاب نشده است');
            return;
        }

        setUploading(true);

        try {
            const formData = new FormData();
            const validFiles = [];

            // بررسی و اضافه کردن فایل‌های معتبر
            const errors = [];
            let totalSize = 0;
            
            for (const file of files) {
                const error = validateFile(file);
                if (error) {
                    errors.push(`${file.name}: ${error}`);
                    continue;
                }
                formData.append('files', file);
                validFiles.push(file);
                totalSize += file.size;
            }

            // نمایش خطاها
            if (errors.length > 0) {
                alert(
                    `⚠️ برخی فایل‌ها معتبر نیستند:\n\n` +
                    errors.join('\n')
                );
            }

            if (validFiles.length === 0) {
                setUploading(false);
                return;
            }
            
            // نمایش اطلاعات آپلود
            console.log(
                `📤 آپلود ${validFiles.length} عکس (حجم کل: ${(totalSize / 1024 / 1024).toFixed(2)}MB)`
            );

            // Upload to backend
            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/api/tenants/${tenantId}/properties/${propertyId}/images`,
                {
                    method: 'POST',
                    headers: getAuthHeaders(),
                    body: formData
                }
            );

            if (!response.ok) {
                const error = await response.json();
                // نمایش خطای دقیق از backend
                const errorMessage = error.detail?.error || error.detail || 'آپلود ناموفق بود';
                throw new Error(errorMessage);
            }

            const data = await response.json();
            
            // Update preview with uploaded images
            const newImages = data.files || [];
            const updatedImages = [...previewImages, ...newImages];
            setPreviewImages(updatedImages);
            
            // Notify parent
            if (onImagesChange) {
                onImagesChange(updatedImages);
            }

            // نمایش پیام موفقیت با جزئیات
            let successMessage = `✅ ${data.uploaded} عکس با موفقیت آپلود شد!\n\n`;
            successMessage += `📊 مجموع عکس‌ها: ${data.total_images}/${data.max_allowed}\n`;
            successMessage += `📍 باقی‌مانده: ${data.remaining_slots} عکس`;
            
            // اگر برخی فایل‌ها آپلود نشدند
            if (data.warnings && data.warnings.failed_files) {
                const failedCount = data.warnings.failed_files.length;
                successMessage += `\n\n⚠️ ${failedCount} فایل آپلود نشد:\n`;
                data.warnings.failed_files.forEach(f => {
                    successMessage += `\n• ${f.filename}: ${f.error}`;
                });
            }
            
            alert(successMessage);
        } catch (error) {
            console.error('❌ خطا در آپلود:', error);
            
            // نمایش خطای دقیق
            let errorMessage = '❌ خطا در آپلود عکس\n\n';
            
            if (error.message) {
                errorMessage += error.message;
            } else {
                errorMessage += 'لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.';
            }
            
            alert(errorMessage);
        } finally {
            setUploading(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        const files = Array.from(e.dataTransfer.files);
        if (files && files.length > 0) {
            uploadImages(files);
        }
    };

    const handleFileInput = (e) => {
        const files = Array.from(e.target.files);
        if (files && files.length > 0) {
            uploadImages(files);
        }
    };

    const deleteImage = async (filename) => {
        if (!confirm('آیا مطمئن هستید می‌خواهید این عکس را حذف کنید؟')) return;

        try {
            const response = await fetch(
                `${import.meta.env.VITE_API_URL}/api/tenants/${tenantId}/properties/${propertyId}/images/${filename}`,
                {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                }
            );

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail?.message || error.detail || 'حذف ناموفق بود');
            }

            // Remove from preview - اصلاح: مقایسه دقیق filename
            const updated = previewImages.filter(img => {
                const imgFilename = typeof img === 'string' 
                    ? img.split('/').pop() 
                    : (img.filename || img.url?.split('/').pop());
                return imgFilename !== filename;
            });
            setPreviewImages(updated);
            
            if (onImagesChange) {
                onImagesChange(updated);
            }

            alert('✅ عکس با موفقیت حذف شد');
        } catch (error) {
            console.error('❌ خطا در حذف:', error);
            alert(`❌ خطا در حذف عکس: ${error.message}`);
        }
    };

    const getImageUrl = (image) => {
        if (typeof image === 'string') return image;
        return image.url || '';
    };

    return (
        <div className="space-y-4">
            {/* Upload Area */}
            <div
                className={`
                    relative border-2 border-dashed rounded-xl p-8 text-center
                    transition-all duration-200
                    ${dragActive ? 'border-gold-500 bg-gold-500/10' : 'border-gray-600 hover:border-gold-500/50'}
                    ${uploading ? 'opacity-50 pointer-events-none' : ''}
                `}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
            >
                <input
                    type="file"
                    id="file-upload"
                    multiple
                    accept="image/*"
                    onChange={handleFileInput}
                    className="hidden"
                    disabled={uploading || !propertyId}
                />
                
                <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="w-12 h-12 mx-auto mb-4 text-gold-500" />
                    <p className="text-lg font-medium text-gray-200 mb-2">
                        {uploading ? 'Uploading...' : 'Drag & Drop Images'}
                    </p>
                    <p className="text-sm text-gray-400">
                        or click to browse • Max {MAX_IMAGES} images • {MAX_FILE_SIZE / 1024 / 1024}MB each
                    </p>
                    <p className="text-xs text-gray-500 mt-2">
                        {previewImages.length} / {MAX_IMAGES} images uploaded
                    </p>
                </label>
            </div>

            {/* Image Grid */}
            {previewImages.length > 0 && (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
                    {previewImages.map((image, index) => {
                        const imgUrl = getImageUrl(image);
                        const filename = typeof image === 'string' ? imgUrl.split('/').pop() : image.filename;
                        
                        return (
                            <div
                                key={index}
                                className="relative group aspect-square rounded-xl overflow-hidden bg-gray-800 border border-gray-700"
                            >
                                <img
                                    src={imgUrl}
                                    alt={`Property ${index + 1}`}
                                    className="w-full h-full object-cover"
                                    onError={(e) => {
                                        e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg"/>';
                                    }}
                                />
                                
                                {/* Overlay with actions */}
                                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                    <button
                                        onClick={() => deleteImage(filename)}
                                        className="p-2 bg-red-600 hover:bg-red-700 rounded-lg text-white transition-colors"
                                        title="Delete image"
                                    >
                                        <Trash2 className="w-5 h-5" />
                                    </button>
                                </div>

                                {/* Primary badge */}
                                {index === 0 && (
                                    <div className="absolute top-2 left-2 bg-gold-500 text-black text-xs px-2 py-1 rounded-md flex items-center gap-1">
                                        <Star className="w-3 h-3 fill-current" />
                                        Primary
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Empty State */}
            {previewImages.length === 0 && !uploading && (
                <div className="text-center py-8 text-gray-500">
                    <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>No images uploaded yet</p>
                    <p className="text-sm mt-2">Upload up to {MAX_IMAGES} property images</p>
                </div>
            )}
        </div>
    );
};

export default PropertyImageUpload;
