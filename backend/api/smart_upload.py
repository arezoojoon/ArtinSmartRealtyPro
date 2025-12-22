"""
Smart Property Upload API
Agents upload PDFs/images → System auto-extracts property details
🔔 NEW: Auto-notifies qualified leads when property matches their preferences
"""

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
import os
import shutil
from pathlib import Path
from datetime import datetime
import logging

from database import async_session, Tenant, TenantProperty, get_db
from property_extractor import PropertyExtractor
from followup_matcher import get_matching_leads_count  # For preview count

router = APIRouter(prefix="/api/tenants", tags=["Smart Upload"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = Path("uploads/properties")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Initialize extractor - PropertyExtractor handles key rotation and retry logic internally
extractor = PropertyExtractor()
logger.info("🚀 PropertyExtractor initialized with AI support")


async def verify_tenant_access(
    credentials: HTTPAuthorizationCredentials,
    tenant_id: int,
    db: AsyncSession
) -> Tenant:
    """Verify tenant authentication"""
    import jwt
    from auth_config import JWT_SECRET, JWT_ALGORITHM
    
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth_tenant_id = payload.get("tenant_id")
    
    # Super Admin can access any tenant
    if auth_tenant_id == 0:
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tenant
    
    # Regular tenant can only access their own data
    if auth_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return tenant


@router.post("/{tenant_id}/properties/smart-upload")
async def smart_upload_property(
    tenant_id: int,
    file: UploadFile = File(..., description="PDF brochure or property image"),
    use_ai: bool = Form(True, description="Use GPT-4 Vision for better extraction (recommended)"),
    auto_save: bool = Form(False, description="Automatically save to database without review"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    🚀 SMART UPLOAD - Just drop a file and we extract everything!
    
    Accepts:
    - PDF brochures (Emaar, Damac, Binghatti, etc.)
    - Property images/flyers
    - Screenshots from Bayut/Property Finder
    
    Returns:
    - Extracted property data (ready to review or auto-save)
    - Confidence score
    - Missing fields warnings
    
    Uses Gemini Vision AI (FREE!) for best quality extraction.
    
    Example:
        Upload "marina-tower-brochure.pdf" → System extracts:
        ✅ Name: Marina Heights Tower
        ✅ Price: 2,500,000 AED
        ✅ Area: 1,450 sqft
        ✅ Bedrooms: 2
        ✅ Location: Dubai Marina
        ✅ ROI: 8.5%
    """
    
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    # Validate file type
    allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.webp'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"tenant_{tenant_id}_{timestamp}_{file.filename}"
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"📁 Saved file: {safe_filename}")
        
    except Exception as e:
        logger.error(f"❌ File save failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {e}")
    
    # Extract property information
    try:
        if file_ext == '.pdf':
            logger.info(f"📄 Extracting from PDF: {file_path}")
            extracted_data = await extractor.extract_from_pdf(str(file_path))
            logger.info(f"📊 PDF Extraction result: {extracted_data}")
        else:
            logger.info(f"🖼️ Extracting from image (AI={use_ai})...")
            extracted_data = await extractor.extract_from_image(str(file_path), use_ai=use_ai)
            logger.info(f"📊 Image Extraction result: {extracted_data}")
        
        # Check for extraction errors
        if 'error' in extracted_data:
            logger.error(f"❌ Extraction returned error: {extracted_data['error']}")
            return {
                'success': False,
                'error': extracted_data['error'],
                'file_path': str(file_path),
                'suggestion': 'Try uploading a clearer image or use AI extraction (use_ai=true)'
            }
        
        # Validate extraction
        is_valid, missing_fields = extractor.validate_extraction(extracted_data)
        logger.info(f"✔️ Validation: is_valid={is_valid}, missing={missing_fields}")
        
        # Calculate confidence score
        total_fields = 10
        filled_fields = sum(1 for v in extracted_data.values() if v and v != [] and v != '')
        confidence = (filled_fields / total_fields) * 100
        
        logger.info(f"✅ Extraction complete: {filled_fields}/{total_fields} fields, {confidence:.1f}% confidence")
        
        # Auto-save if requested and valid
        property_id = None
        if auto_save and is_valid:
            property_id = await _save_property_to_db(
                tenant_id=tenant_id,
                extracted_data=extracted_data,
                file_path=str(file_path),
                db=db
            )
            logger.info(f"💾 Auto-saved property ID: {property_id}")
        
        return {
            'success': True,
            'confidence': round(confidence, 1),
            'is_valid': is_valid,
            'missing_fields': missing_fields if missing_fields else [],
            'extracted_data': extracted_data,
            'property_id': property_id,
            'file_path': str(file_path),
            'auto_saved': auto_save and is_valid,
            'message': (
                f"✅ Property auto-saved with {confidence:.1f}% confidence!" 
                if auto_save and is_valid 
                else f"📋 Extracted with {confidence:.1f}% confidence. Review and save manually."
            )
        }
        
    except Exception as e:
        logger.error(f"❌ Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")


@router.post("/{tenant_id}/properties/batch-upload")
async def batch_upload_properties(
    tenant_id: int,
    files: List[UploadFile] = File(..., description="Multiple PDF/image files"),
    use_ai: bool = Form(True),
    auto_save: bool = Form(True, description="Auto-save all valid properties"),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    🔥 BATCH UPLOAD - Upload 10+ property brochures at once!
    
    Perfect for:
    - Importing entire Emaar catalog
    - Adding all Damac projects
    - Bulk import from PropertyFinder
    
    Returns:
    - Total uploaded
    - Successfully extracted
    - Auto-saved count
    - Failed items with reasons
    """
    
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    results = {
        'total': len(files),
        'successful': 0,
        'auto_saved': 0,
        'failed': 0,
        'items': []
    }
    
    for file in files:
        try:
            # Process each file
            result = await smart_upload_property(
                tenant_id=tenant_id,
                file=file,
                use_ai=use_ai,
                auto_save=auto_save,
                credentials=credentials,
                db=db
            )
            
            if result['success']:
                results['successful'] += 1
                if result.get('auto_saved'):
                    results['auto_saved'] += 1
            else:
                results['failed'] += 1
            
            results['items'].append({
                'filename': file.filename,
                'success': result['success'],
                'confidence': result.get('confidence'),
                'property_id': result.get('property_id'),
                'error': result.get('error')
            })
            
        except Exception as e:
            results['failed'] += 1
            results['items'].append({
                'filename': file.filename,
                'success': False,
                'error': str(e)
            })
    
    logger.info(f"📦 Batch upload complete: {results['successful']}/{results['total']} successful")
    
    return results


@router.post("/{tenant_id}/properties/save-extracted")
async def save_extracted_property(
    tenant_id: int,
    extracted_data: dict,
    file_path: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Save reviewed/edited property data to database
    
    Use this after smart-upload to save manually reviewed data
    """
    
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    try:
        property_id = await _save_property_to_db(
            tenant_id=tenant_id,
            extracted_data=extracted_data,
            file_path=file_path,
            db=db
        )
        
        return {
            'success': True,
            'property_id': property_id,
            'message': f'Property saved successfully (ID: {property_id})'
        }
        
    except Exception as e:
        logger.error(f"❌ Save failed: {e}")
        raise HTTPException(status_code=500, detail=f"Save failed: {e}")


@router.post("/{tenant_id}/properties/{property_id}/notify-leads")
async def notify_leads_of_property(
    tenant_id: int,
    property_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    🔔 NOTIFY QUALIFIED LEADS - Send property to matching leads
    
    After uploading a property, use this endpoint to automatically:
    - Find qualified leads with matching preferences (budget, type, bedrooms)
    - Send property presentation with photos + ROI PDF
    - Include urgency messaging (scarcity, social proof, time pressure)
    
    Note: Requires bot to be running (Telegram or WhatsApp)
    
    Returns:
    - leads_notified: Number of leads successfully notified
    - matching_leads: Total matching leads found
    - errors: List of errors encountered
    """
    
    # Verify access
    tenant = await verify_tenant_access(credentials, tenant_id, db)
    
    try:
        # Import here to avoid circular dependency
        from followup_matcher import notify_qualified_leads_of_new_property
        
        # Get bot interface - try Telegram first, then WhatsApp
        bot_interface = None
        
        # Try to get Telegram bot
        try:
            from telegram_bot import TelegramBot
            bot_interface = TelegramBot(tenant)
            platform = "telegram"
        except Exception as telegram_error:
            logger.warning(f"⚠️ Telegram bot not available: {telegram_error}")
            
            # Try WhatsApp as fallback
            try:
                from whatsapp_bot import WhatsAppBot
                bot_interface = WhatsAppBot(tenant)
                platform = "whatsapp"
            except Exception as wa_error:
                logger.warning(f"⚠️ WhatsApp bot not available: {wa_error}")
        
        if not bot_interface:
            raise HTTPException(
                status_code=503, 
                detail="No bot interface available. Make sure Telegram or WhatsApp bot is running."
            )
        
        # Trigger follow-up notifications
        stats = await notify_qualified_leads_of_new_property(
            tenant_id=tenant_id,
            property_id=property_id,
            bot_interface=bot_interface
        )
        
        return {
            'success': True,
            'platform': platform,
            'leads_notified': stats['leads_notified'],
            'leads_skipped': stats['leads_skipped'],
            'errors': stats['errors'],
            'message': (
                f"✅ Notified {stats['leads_notified']} qualified leads via {platform}!" 
                if stats['leads_notified'] > 0 
                else "ℹ️ No qualified leads match this property yet"
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Notification failed: {e}")
        raise HTTPException(status_code=500, detail=f"Notification failed: {e}")


async def _save_property_to_db(
    tenant_id: int,
    extracted_data: dict,
    file_path: Optional[str],
    db: AsyncSession
) -> int:
    """Helper: Save extracted property to database"""
    
    # Get BASE_URL from environment or use default
    base_url = os.getenv('BASE_URL', 'http://localhost:8000')
    
    # Handle images
    primary_image = extracted_data.get('primary_image')
    image_urls = []
    brochure_pdf = None
    
    # If file was uploaded, convert to accessible URL
    if file_path:
        filename = Path(file_path).name
        file_url = f"{base_url}/uploads/properties/{filename}"
        
        # Check if it's an image or PDF
        if file_path.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            if not primary_image:
                primary_image = file_url
            image_urls.append(file_url)
        elif file_path.endswith('.pdf'):
            brochure_pdf = file_url
    
    # Add any extracted image URLs
    if extracted_data.get('images'):
        for img in extracted_data['images']:
            if img and img.startswith('http'):
                image_urls.append(img)
    
    # Ensure primary_image is set
    if not primary_image:
        if image_urls:
            primary_image = image_urls[0]
        else:
            # Default placeholder
            primary_image = "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800"
            image_urls.append(primary_image)
    
    # Create property record
    new_property = TenantProperty(
        tenant_id=tenant_id,
        name=extracted_data.get('name') or 'Untitled Property',
        description=extracted_data.get('description'),
        price=extracted_data.get('price') or 0,
        location=extracted_data.get('location') or 'Dubai',
        area_sqft=extracted_data.get('area_sqft'),
        bedrooms=extracted_data.get('bedrooms'),
        bathrooms=extracted_data.get('bathrooms'),
        property_type=extracted_data.get('property_type') or 'APARTMENT',
        transaction_type=extracted_data.get('transaction_type') or 'BUY',
        expected_roi=extracted_data.get('roi_percentage'),
        golden_visa_eligible=extracted_data.get('is_golden_visa_eligible', False),
        primary_image=primary_image,
        image_urls=image_urls,  # Array of all images
        brochure_pdf=brochure_pdf,  # PDF brochure if uploaded
        features=extracted_data.get('amenities', []),
        full_description=extracted_data.get('payment_plan'),  # Store payment plan in description
        is_available=True,
        is_featured=False
    )
    
    db.add(new_property)
    await db.commit()
    await db.refresh(new_property)
    
    logger.info(f"💾 Saved property: {new_property.name} (ID: {new_property.id})")
    logger.info(f"📸 Images: {len(image_urls)} | 📄 PDF: {'Yes' if brochure_pdf else 'No'}")
    
    # 🔔 Check how many qualified leads match this property
    matching_count = await get_matching_leads_count(tenant_id, new_property.id)
    if matching_count > 0:
        logger.info(f"🎯 {matching_count} qualified leads match this property - ready for follow-up!")
    else:
        logger.info(f"ℹ️ No qualified leads match this property yet")
    
    return new_property.id
