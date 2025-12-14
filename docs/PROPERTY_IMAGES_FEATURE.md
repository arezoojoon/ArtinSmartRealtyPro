# 📸 Property Images Feature

## Overview
Multi-image upload system for property listings with drag-and-drop interface, supporting up to 5 images per property with automatic file management and cleanup.

---

## ✨ Features

### 🖼️ Image Management
- **Multi-Upload**: Upload up to 5 images per property
- **Drag & Drop**: Intuitive drag-and-drop interface
- **File Validation**: 
  - Max file size: 5MB per image
  - Allowed formats: .jpg, .jpeg, .png, .webp
  - Max images: 5 per property
- **Preview Grid**: Visual preview with hover actions
- **Delete Individual**: Remove specific images with confirmation
- **Primary Image**: First uploaded image automatically set as primary
- **Auto Cleanup**: Orphaned files removed on property deletion

### 📝 Rich Text Descriptions
- **Full Description Field**: Support for emoji-rich, formatted property descriptions
- **RTL Support**: Right-to-left text direction for Persian/Arabic content
- **Example Format**:
  ```
  🏠 ویلا مدرن در شمال تهران
  📍 محدوده: سعادت آباد
  📏 متراژ: 250 متر
  🛏️ 3 خوابه + 3 سرویس
  ✨ امکانات: پارکینگ، انباری، آسانسور
  💰 قیمت: تماس بگیرید
  🔥 فروش فوری
  ```

### 🚨 Urgent Sale Flag
- **Checkbox**: Mark properties as "Urgent Sale"
- **Database Flag**: `is_urgent` boolean field
- **Visual Indicator**: 🔥 emoji in listings

---

## 🗄️ Database Schema

### New Fields Added to `tenant_properties`

```sql
-- Image URLs array
image_urls JSON DEFAULT '[]'::json

-- Image metadata (filename, size, url, hash, uploaded_at)
image_files JSON DEFAULT '[]'::json

-- Primary display image URL
primary_image VARCHAR(512)

-- Rich formatted description with emojis
full_description TEXT

-- Urgent sale flag
is_urgent BOOLEAN DEFAULT FALSE
```

### Migration

Run the migration script to add new columns:

```bash
cd backend
python migrate_property_images.py
```

**Note**: Database must be running. If using Docker:
```bash
docker-compose up -d postgres
```

---

## 🔧 Backend Implementation

### File Storage Structure

```
uploads/
└── properties/
    └── tenant_{tenant_id}/
        └── property_{property_id}/
            ├── {unique_hash}_{timestamp}.jpg
            ├── {unique_hash}_{timestamp}.png
            └── ...
```

### API Endpoints

#### 1. Upload Images
```http
POST /api/tenants/{tenant_id}/properties/{property_id}/images
Content-Type: multipart/form-data

files: [File, File, ...]
```

**Response**:
```json
{
  "message": "Uploaded 3 image(s)",
  "files": [
    {
      "filename": "abc123_20240101.jpg",
      "url": "/uploads/properties/tenant_1/property_5/abc123_20240101.jpg",
      "size": 245678,
      "uploaded_at": "2024-01-01T12:00:00"
    }
  ]
}
```

#### 2. Delete Image
```http
DELETE /api/tenants/{tenant_id}/properties/{property_id}/images/{filename}
```

**Response**:
```json
{
  "message": "Image deleted successfully",
  "deleted_file": "abc123_20240101.jpg"
}
```

### File Manager Service

**Location**: `backend/file_manager.py`

**Key Methods**:
- `save_property_image()`: Validate and save image with unique filename
- `delete_property_image()`: Remove single image from filesystem
- `delete_property_images()`: Batch delete from metadata
- `cleanup_property_directory()`: Remove all images for a property
- `cleanup_old_files()`: Remove orphaned files older than N days

**Validation**:
```python
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGES_PER_PROPERTY = 5
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
```

---

## 🎨 Frontend Implementation

### PropertyImageUpload Component

**Location**: `frontend/src/components/PropertyImageUpload.jsx`

**Props**:
```jsx
<PropertyImageUpload
  propertyId={editingProperty?.id}
  tenantId={editingProperty?.tenant_id}
  images={formData.image_urls || []}
  onImagesChange={(newImages) => {
    setFormData({ ...formData, image_urls: newImages });
  }}
/>
```

**Features**:
- Drag-and-drop upload zone
- File validation (client-side)
- Upload progress indication
- Grid preview (2 columns)
- Hover overlay with delete button
- Primary image badge
- Empty state message

### PropertiesManagement Updates

**New Form Fields**:
1. **Full Description** - Large textarea with RTL support
2. **Urgent Sale Checkbox** - Boolean flag with emoji
3. **Property Images** - PropertyImageUpload component

**FormData Structure**:
```javascript
{
  name: '',
  description: '',
  full_description: '',  // NEW: Rich text with emojis
  is_urgent: false,      // NEW: Urgent sale flag
  image_urls: [],        // NEW: Array of image URLs
  // ... other fields
}
```

---

## 🧪 Testing

### Test Plan

1. **Create Property → Upload Images**
   ```
   ✓ Create new property
   ✓ Save property
   ✓ Upload 1-5 images
   ✓ Verify images appear in preview
   ✓ Check database: image_urls, image_files updated
   ✓ Check filesystem: files saved in correct directory
   ```

2. **Delete Image**
   ```
   ✓ Click delete on any image
   ✓ Confirm deletion
   ✓ Verify image removed from preview
   ✓ Check database: image_urls updated
   ✓ Check filesystem: file deleted
   ✓ If primary deleted: next image becomes primary
   ```

3. **Delete Property**
   ```
   ✓ Delete property
   ✓ Check database: property record removed
   ✓ Check filesystem: property directory deleted
   ✓ Verify all images removed
   ```

4. **Validation Tests**
   ```
   ✓ Upload > 5 images → Error
   ✓ Upload > 5MB file → Error
   ✓ Upload non-image file → Error
   ✓ Upload without saving property first → Error
   ```

5. **Full Description Test**
   ```
   ✓ Enter emoji-rich description
   ✓ Save property
   ✓ Reload page
   ✓ Verify description preserved with emojis
   ✓ Check RTL text alignment
   ```

### Manual Testing Steps

**Start Backend**:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Start Frontend**:
```bash
cd frontend
npm run dev
```

**Test Workflow**:
1. Login as tenant admin
2. Navigate to Properties Management
3. Click "Add Property"
4. Fill in property details
5. Add full_description with emojis: `🏠 Modern Villa\n📍 Location: Dubai\n💰 Price: 1M AED`
6. Check "Urgent Sale"
7. Save property
8. Upload 3 images via drag-and-drop
9. Verify preview shows all 3 images
10. Delete one image
11. Verify preview updates
12. Edit property → check all fields persist
13. Delete property → verify files cleaned up

---

## 🐛 Troubleshooting

### Database Connection Issues

**Error**: `The remote computer refused the network connection`

**Solution**:
1. Check PostgreSQL is running:
   ```bash
   docker-compose ps
   ```
2. Start database if needed:
   ```bash
   docker-compose up -d postgres
   ```
3. Verify connection in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/artinrealty
   ```

### Migration Fails

**Error**: `greenlet_spawn has not been called`

**Solution**: Use the async migration script provided (`migrate_property_images.py`)

### Upload Fails - "Property must be saved first"

**Cause**: Trying to upload images before property is created

**Solution**: Save property first, then upload images in edit mode

### Images Don't Display

**Checks**:
1. Static files mounted in `main.py`:
   ```python
   app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
   ```
2. UPLOAD_DIR exists and is writable:
   ```python
   UPLOAD_DIR = Path(__file__).parent / "uploads"
   UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
   ```
3. Frontend uses correct API URL:
   ```javascript
   const url = `${import.meta.env.VITE_API_URL}/api/...`
   ```

### File Permissions Error

**Linux/Mac**:
```bash
chmod -R 755 backend/uploads
```

**Windows**: Ensure IIS_IUSRS or equivalent has write permissions

---

## 📋 TODO / Future Enhancements

- [ ] **Image Optimization**: Compress images on upload (e.g., with Pillow)
- [ ] **Thumbnails**: Generate thumbnails for faster loading
- [ ] **Reorder Images**: Drag to reorder, not just first = primary
- [ ] **Bulk Upload**: Select folder to upload all images
- [ ] **Cloud Storage**: S3/Azure Blob for production
- [ ] **Image Cropping**: Client-side crop tool before upload
- [ ] **Watermarking**: Auto-add agency logo to images
- [ ] **Cleanup Cron**: Background job to remove orphaned files > 30 days
- [ ] **Image Metadata**: Extract EXIF data (dimensions, GPS, etc.)
- [ ] **CDN Integration**: Serve images via CDN for better performance

---

## 🔐 Security Considerations

1. **File Type Validation**: Server-side MIME type checking (not just extension)
2. **File Size Limits**: Enforce 5MB max per file
3. **Path Traversal**: Use `secure_filename()` or hash-based naming
4. **Authentication**: All endpoints require valid JWT token
5. **Authorization**: Tenant isolation - can only access own properties
6. **Virus Scanning**: Consider ClamAV for production
7. **Rate Limiting**: Prevent abuse of upload endpoint

---

## 📚 Related Files

### Backend
- `backend/main.py` - API endpoints (upload, delete)
- `backend/database.py` - TenantProperty model with image fields
- `backend/file_manager.py` - File storage service
- `backend/migrate_property_images.py` - Database migration script

### Frontend
- `frontend/src/components/PropertyImageUpload.jsx` - Upload component
- `frontend/src/components/PropertiesManagement.jsx` - Property CRUD with images

### Documentation
- `docs/PROPERTY_IMAGES_FEATURE.md` - This file

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review console logs (frontend + backend)
3. Verify database schema matches expected structure
4. Check file permissions on uploads directory

---

**Last Updated**: 2024-01-01  
**Version**: 1.0.0  
**Author**: ArtinSmartRealty Development Team
