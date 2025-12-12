"""
Property Media Handler
Handles sending property photos and PDFs to users
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_

from database import TenantProperty, PropertyType, TransactionType

logger = logging.getLogger(__name__)


async def get_property_media(
    tenant_id: int,
    property_id: Optional[int] = None,
    property_type: Optional[str] = None,
    location: Optional[str] = None,
    max_price: Optional[float] = None,
    bedrooms: Optional[int] = None,
    limit: int = 5,
    db: Optional[AsyncSession] = None
) -> List[Dict]:
    """
    Get property media (images + PDF) based on filters
    
    Args:
        tenant_id: Tenant ID
        property_id: Specific property ID (if provided, returns only that property)
        property_type: Filter by property type
        location: Filter by location
        max_price: Maximum price filter
        bedrooms: Number of bedrooms
        limit: Max number of properties to return
        db: Database session
        
    Returns:
        List of property media objects with images and PDF
    """
    if db is None:
        raise ValueError("Database session is required")
        
    try:
        query = select(TenantProperty).where(
            and_(
                TenantProperty.tenant_id == tenant_id,
                TenantProperty.is_available == True
            )
        )
        
        # Filter by specific property ID
        if property_id:
            query = query.where(TenantProperty.id == property_id)
        
        # Filter by property type
        if property_type:
            query = query.where(TenantProperty.property_type == property_type)
        
        # Filter by location (case-insensitive partial match)
        if location:
            query = query.where(TenantProperty.location.ilike(f"%{location}%"))
        
        # Filter by price
        if max_price:
            query = query.where(
                or_(
                    TenantProperty.price <= max_price,
                    TenantProperty.price.is_(None)
                )
            )
        
        # Filter by bedrooms
        if bedrooms:
            query = query.where(TenantProperty.bedrooms == bedrooms)
        
        # Order by featured, then created date
        query = query.order_by(
            TenantProperty.is_featured.desc(),
            TenantProperty.created_at.desc()
        ).limit(limit)
        
        result = await db.execute(query)
        properties = result.scalars().all()
        
        media_list = []
        for prop in properties:
            # Prepare images
            images = []
            
            # Add primary image first (check if not None)
            primary_img = getattr(prop, 'primary_image', None)
            if primary_img is not None and primary_img:
                images.append({
                    'url': primary_img,
                    'type': 'image',
                    'is_primary': True
                })
            
            # Add image URLs
            image_urls_val = getattr(prop, 'image_urls', None)
            if image_urls_val is not None and image_urls_val:
                for url in image_urls_val:
                    if url and url != primary_img:  # Don't duplicate primary
                        images.append({
                            'url': url,
                            'type': 'image',
                            'is_primary': False
                        })
            
            # Add image files
            image_files_val = getattr(prop, 'image_files', None)
            if image_files_val is not None and image_files_val:
                for img in image_files_val:
                    if isinstance(img, dict) and img.get('url'):
                        url = img['url']
                        if url not in [i['url'] for i in images]:  # Avoid duplicates
                            images.append({
                                'url': url,
                                'type': 'image',
                                'is_primary': False,
                                'filename': img.get('filename'),
                                'size': img.get('size')
                            })
            
            # Add PDF brochure
            pdf = None
            brochure_pdf_val = getattr(prop, 'brochure_pdf', None)
            if brochure_pdf_val is not None and brochure_pdf_val:
                pdf = {
                    'url': brochure_pdf_val,
                    'type': 'pdf',
                    'name': f"{prop.name}_Brochure.pdf"
                }
            
            media_obj = {
                'property_id': prop.id,
                'property_name': prop.name,
                'property_type': str(prop.property_type.value) if hasattr(prop.property_type, 'value') else None,
                'location': prop.location,
                'price': prop.price,
                'bedrooms': prop.bedrooms,
                'bathrooms': prop.bathrooms,
                'area_sqft': prop.area_sqft,
                'description': prop.description or prop.full_description,
                'images': images,  # List of image dicts
                'pdf': pdf,  # Single PDF dict or None
                'features': prop.features or [],
                'is_featured': prop.is_featured,
                'url': f"/properties/{prop.id}"  # Link to full property page
            }
            
            media_list.append(media_obj)
        
        logger.info(f"✅ Found {len(media_list)} properties with media for tenant {tenant_id}")
        return media_list
        
    except Exception as e:
        logger.error(f"❌ Error fetching property media: {e}")
        return []


async def format_property_for_message(property_media: Dict, language: str = "en") -> str:
    """
    Format property data for chat message
    
    Args:
        property_media: Property media dict from get_property_media
        language: Message language (en, fa, ar, ru)
        
    Returns:
        Formatted message string
    """
    try:
        templates = {
            'en': """🏠 **{name}**

📍 Location: {location}
💰 Price: AED {price:,.0f}
🛏️ Bedrooms: {bedrooms}
🚿 Bathrooms: {bathrooms}
📐 Area: {area} sqft
{features}
{description}

{media_info}""",
            'fa': """🏠 **{name}**

📍 موقعیت: {location}
💰 قیمت: {price:,.0f} درهم
🛏️ اتاق خواب: {bedrooms}
🚿 حمام: {bathrooms}
📐 متراژ: {area} فوت مربع
{features}
{description}

{media_info}""",
            'ar': """🏠 **{name}**

📍 الموقع: {location}
💰 السعر: {price:,.0f} درهم
🛏️ غرف النوم: {bedrooms}
🚿 الحمامات: {bathrooms}
📐 المساحة: {area} قدم مربع
{features}
{description}

{media_info}"""
        }
        
        template = templates.get(language, templates['en'])
        
        # Format features
        features_text = ""
        if property_media.get('features'):
            features_list = property_media['features']
            if language == 'fa':
                features_text = f"✨ امکانات: {', '.join(features_list)}"
            elif language == 'ar':
                features_text = f"✨ المميزات: {', '.join(features_list)}"
            else:
                features_text = f"✨ Features: {', '.join(features_list)}"
        
        # Format media info
        media_info_parts = []
        image_count = len(property_media.get('images', []))
        has_pdf = property_media.get('pdf') is not None
        
        if image_count > 0:
            if language == 'fa':
                media_info_parts.append(f"📸 {image_count} عکس")
            elif language == 'ar':
                media_info_parts.append(f"📸 {image_count} صورة")
            else:
                media_info_parts.append(f"📸 {image_count} photo(s)")
        
        if has_pdf:
            if language == 'fa':
                media_info_parts.append("📄 بروشور PDF")
            elif language == 'ar':
                media_info_parts.append("📄 كتيب PDF")
            else:
                media_info_parts.append("📄 PDF Brochure")
        
        media_info = " | ".join(media_info_parts) if media_info_parts else ""
        
        message = template.format(
            name=property_media['property_name'],
            location=property_media['location'],
            price=property_media.get('price', 0) or 0,
            bedrooms=property_media.get('bedrooms') or 'N/A',
            bathrooms=property_media.get('bathrooms') or 'N/A',
            area=property_media.get('area_sqft') or 'N/A',
            features=features_text,
            description=property_media.get('description', ''),
            media_info=media_info
        )
        
        return message.strip()
        
    except Exception as e:
        logger.error(f"❌ Error formatting property message: {e}")
        return f"🏠 {property_media.get('property_name', 'Property')}"
