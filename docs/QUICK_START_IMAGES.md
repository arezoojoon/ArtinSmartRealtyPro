# 🚀 Quick Start: Property Images Feature

## Prerequisites
- PostgreSQL database running
- Backend dependencies installed
- Frontend dependencies installed

## Step 1: Database Migration

```bash
# Navigate to backend
cd backend

# Run migration (add image columns)
python migrate_property_images.py
```

**Expected Output**:
```
============================================================
Property Images Migration Script
============================================================

🔄 Starting migration: Add image support to tenant_properties table
  ➜ Add image_urls column... ✅
  ➜ Add image_files column... ✅
  ➜ Add primary_image column... ✅
  ➜ Add full_description column... ✅
  ➜ Add is_urgent column... ✅

✅ Migration completed successfully!

🔍 Verifying migration...
✅ All columns present:
  - full_description (text)
  - image_files (json)
  - image_urls (json)
  - is_urgent (boolean)
  - primary_image (character varying)
```

## Step 2: Start Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

**Verify**: Visit http://localhost:8000/docs to see API documentation

## Step 3: Start Frontend

```bash
cd frontend
npm run dev
```

**Verify**: Visit http://localhost:5173 (or shown port)

## Step 4: Test Image Upload

### A. Create Property with Images

1. **Login** to tenant dashboard
2. Navigate to **Properties Management**
3. Click **"Add New Property"**
4. Fill in basic details:
   - Name: `Modern Villa in Dubai`
   - Type: `VILLA`
   - Transaction: `BUY`
   - Location: `Dubai Marina`
   - Price: `2500000`

5. Add **Full Description** with emojis:
   ```
   🏠 ویلا مدرن در دبی
   📍 محدوده: دبی مارینا
   📏 متراژ: 350 متر
   🛏️ 4 خوابه + 5 سرویس
   ✨ امکانات:
   • پارکینگ دوبل
   • استخر اختصاصی
   • جیم و سونا
   • نمای دریا
   💰 قیمت: 2.5 میلیون AED
   🔥 فروش فوری - تخفیف ویژه
   ```

6. Check **"🔥 فروش فوری (Urgent Sale)"**

7. Click **"Save"** (property must be saved before uploading images)

8. **Upload Images**:
   - Drag and drop 2-5 images onto the upload zone
   - OR click the zone to select files
   - Wait for upload confirmation

9. Verify:
   - ✅ Images appear in preview grid
   - ✅ First image shows "Primary" badge
   - ✅ Hover shows delete button

### B. Edit Property & Manage Images

1. Click **"Edit"** on the property
2. Verify all fields are populated including full_description
3. **Delete an Image**:
   - Hover over any image
   - Click trash icon
   - Confirm deletion
   - Verify image removed from preview

4. **Add More Images** (if < 5 total):
   - Drag and drop additional images
   - Verify upload success

### C. Delete Property

1. Click **"Delete"** on the property
2. Confirm deletion
3. Verify property removed from list
4. **Check Filesystem** (backend/uploads/properties/):
   - Property folder should be deleted
   - All images should be cleaned up

## Step 5: Validation Tests

### Test Max Images (5)
1. Create/edit a property
2. Try uploading 6 images at once
3. **Expected**: Error message `"Maximum 5 images allowed"`

### Test File Size (5MB)
1. Create a 6MB+ image file
2. Try uploading it
3. **Expected**: Error message `"File size must be less than 5MB"`

### Test File Type
1. Try uploading a PDF or TXT file
2. **Expected**: Error message `"Only image files are allowed"`

### Test Without Saving Property
1. Click "Add New Property"
2. Try uploading images WITHOUT clicking Save first
3. **Expected**: Error message `"Property must be saved before uploading images"`

## Troubleshooting

### Database Not Running
```bash
# Start PostgreSQL with Docker
docker-compose up -d postgres

# Verify it's running
docker-compose ps
```

### Migration Fails
```bash
# Check database connection
psql -h localhost -U postgres -d artinrealty

# If connection works, re-run migration
python migrate_property_images.py
```

### Images Don't Upload
1. Check backend console for errors
2. Verify `uploads/properties/` directory exists and is writable
3. Check browser console for network errors
4. Verify property is saved (has ID) before uploading

### Images Don't Display
1. Check StaticFiles is mounted in `main.py`:
   ```python
   app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
   ```
2. Verify image URLs in browser DevTools Network tab
3. Check CORS settings if frontend on different port

## Success Criteria ✅

You've successfully implemented the feature when:

- ✅ Database migration runs without errors
- ✅ Backend starts with no errors
- ✅ Frontend starts with no errors
- ✅ Can create property with full_description and is_urgent
- ✅ Can upload 1-5 images per property
- ✅ Images display in preview grid
- ✅ Can delete individual images
- ✅ Deleting property removes all its images
- ✅ Validation prevents > 5 images, > 5MB files, non-images
- ✅ Emojis display correctly in full_description
- ✅ Urgent sale checkbox works

## Next Steps

After testing the basic feature:

1. **Performance**: Test with large images (close to 5MB)
2. **Concurrency**: Test multiple users uploading simultaneously
3. **Error Recovery**: Test network failures during upload
4. **Mobile**: Test drag-drop on touch devices
5. **Production**: Configure cloud storage (S3/Azure) for scalability

---

**Need Help?** Check `docs/PROPERTY_IMAGES_FEATURE.md` for detailed documentation.
