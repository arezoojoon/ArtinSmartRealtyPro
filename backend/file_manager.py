"""
File Manager Service for Property Images
Handles upload, storage, cleanup of property images
"""

import os
import shutil
import hashlib
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Configuration - محدودیت‌های امنیتی و بهینه‌سازی دیتابیس
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads/properties")
MAX_FILE_SIZE = 3 * 1024 * 1024  # 3MB per image (کاهش حجم برای دیتابیس)
MAX_IMAGES_PER_PROPERTY = 5  # حداکثر 5 عکس
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}  # بررسی MIME type


class FileManager:
    """Manage property image uploads and cleanup."""
    
    def __init__(self):
        self.upload_dir = Path(UPLOAD_DIR)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_property_image(
        self, 
        file_data: bytes, 
        filename: str, 
        tenant_id: int, 
        property_id: int,
        content_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Save a property image and return metadata.
        محدودیت: حداکثر 3MB حجم، فقط jpg/png/webp
        
        Returns:
            {
                "filename": "unique_filename.jpg",
                "original_filename": "original.jpg",
                "size": 1234567,
                "url": "/uploads/properties/tenant_1/property_5/abc123.jpg",
                "uploaded_at": "2025-11-27T10:30:00",
                "hash": "md5_hash"
            }
        """
        # Validate file size - محدودیت 3MB
        file_size_mb = len(file_data) / 1024 / 1024
        if len(file_data) > MAX_FILE_SIZE:
            raise ValueError(
                f"حجم فایل بیش از حد مجاز است! حداکثر {MAX_FILE_SIZE / 1024 / 1024:.1f}MB مجاز است. "
                f"حجم فایل شما: {file_size_mb:.2f}MB"
            )
        
        # Validate MIME type for security - بررسی امنیتی نوع فایل
        if content_type and content_type not in ALLOWED_MIME_TYPES:
            raise ValueError(
                f"نوع فایل مجاز نیست! فقط عکس‌های JPG, PNG و WebP مجاز هستند. "
                f"نوع فایل شما: {content_type}"
            )
        
        # Validate extension
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(
                f"پسوند فایل مجاز نیست! پسوندهای مجاز: {', '.join(ALLOWED_EXTENSIONS)}. "
                f"پسوند فایل شما: {ext}"
            )
        
        # Create directory structure: uploads/properties/tenant_{id}/property_{id}/
        property_dir = self.upload_dir / f"tenant_{tenant_id}" / f"property_{property_id}"
        property_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename using hash + timestamp
        file_hash = hashlib.md5(file_data).hexdigest()[:12]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file_hash}{ext}"
        
        # Save file
        file_path = property_dir / unique_filename
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        logger.info(f"Saved image: {file_path} ({len(file_data)} bytes)")
        
        # Return metadata
        return {
            "filename": unique_filename,
            "original_filename": filename,
            "size": len(file_data),
            "url": f"/uploads/properties/tenant_{tenant_id}/property_{property_id}/{unique_filename}",
            "path": str(file_path),
            "uploaded_at": datetime.utcnow().isoformat(),
            "hash": file_hash
        }
    
    def delete_property_image(self, file_path: str) -> bool:
        """Delete a property image file."""
        try:
            path = Path(file_path)
            if path.exists() and path.is_file():
                path.unlink()
                logger.info(f"Deleted image: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
        except Exception as e:
            logger.error(f"Failed to delete {file_path}: {e}")
            return False
    
    def delete_property_images(self, file_metadata_list: List[Dict]) -> int:
        """
        Delete multiple property images.
        
        Args:
            file_metadata_list: List of file metadata dicts with 'path' key
        
        Returns:
            Number of files successfully deleted
        """
        if not file_metadata_list:
            logger.warning("هیچ فایلی برای حذف مشخص نشده است")
            return 0
        
        deleted_count = 0
        for file_meta in file_metadata_list:
            # اصلاح: بررسی دقیق‌تر مسیر فایل
            file_path = file_meta.get("path")
            if not file_path:
                # Try to construct path from URL
                url = file_meta.get("url", "")
                if url:
                    # Remove /uploads/ prefix and add upload_dir
                    file_path = str(self.upload_dir / url.replace("/uploads/properties/", ""))
                else:
                    logger.warning(f"مسیر فایل پیدا نشد: {file_meta}")
                    continue
            
            if self.delete_property_image(file_path):
                deleted_count += 1
        
        logger.info(f"حذف {deleted_count} فایل از {len(file_metadata_list)} فایل")
        return deleted_count
    
    def cleanup_property_directory(self, tenant_id: int, property_id: int) -> int:
        """
        Delete all images for a property.
        
        Returns:
            Number of files deleted
        """
        property_dir = self.upload_dir / f"tenant_{tenant_id}" / f"property_{property_id}"
        
        if not property_dir.exists():
            return 0
        
        deleted_count = 0
        try:
            for file_path in property_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()
                    deleted_count += 1
            
            # Remove empty directory
            property_dir.rmdir()
            logger.info(f"Cleaned up property directory: {property_dir} ({deleted_count} files)")
        except Exception as e:
            logger.error(f"Failed to cleanup {property_dir}: {e}")
        
        return deleted_count
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """
        Clean up orphaned files older than specified days.
        Use with caution - should check database first.
        
        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        deleted_count = 0
        
        try:
            for file_path in self.upload_dir.rglob("*"):
                if file_path.is_file():
                    # Check file modification time
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted old file: {file_path}")
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
        
        return deleted_count
    
    def get_property_images(self, tenant_id: int, property_id: int) -> List[str]:
        """Get list of image URLs for a property."""
        property_dir = self.upload_dir / f"tenant_{tenant_id}" / f"property_{property_id}"
        
        if not property_dir.exists():
            return []
        
        image_urls = []
        for file_path in property_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                url = f"/uploads/properties/tenant_{tenant_id}/property_{property_id}/{file_path.name}"
                image_urls.append(url)
        
        return sorted(image_urls)
    
    def validate_image_count(self, current_count: int, new_count: int) -> bool:
        """Check if adding new images would exceed the limit."""
        return (current_count + new_count) <= MAX_IMAGES_PER_PROPERTY


# Global instance
file_manager = FileManager()
