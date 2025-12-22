"""
ArtinSmartRealty - Lead Follow-up Matcher
Automatically notifies qualified leads when new properties match their preferences.

این سیستم:
1. وقتی ملک جدید آپلود میشه، لیدهای کولیفای شده رو پیدا می‌کنه
2. املاکی که با بودجه، نوع ملک، تعداد اتاق مطابقت دارن رو فیلتر می‌کنه
3. پیام فوری با عکس و ROI PDF می‌فرسته
4. urgency messaging استفاده می‌کنه برای بازارگرمی
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from database import (
    Lead, TenantProperty, Tenant, async_session, select,
    Language, LeadStatus, PropertyType
)
from property_presenter import send_property_with_roi
from brain import generate_urgency_message

logger = logging.getLogger(__name__)


async def notify_qualified_leads_of_new_property(
    tenant_id: int,
    property_id: int,
    bot_interface: Any = None  # telegram_bot or whatsapp_bot instance
) -> Dict[str, Any]:
    """
    وقتی ملک جدید آپلود میشه، به لیدهای کولیفای شده اطلاع بده.
    
    Args:
        tenant_id: شناسه tenant
        property_id: شناسه ملک جدید
        bot_interface: instance از telegram_bot یا whatsapp_bot
    
    Returns:
        Dict with stats: {
            "leads_notified": int,
            "leads_skipped": int,
            "errors": List[str]
        }
    """
    stats = {
        "leads_notified": 0,
        "leads_skipped": 0,
        "errors": []
    }
    
    async with async_session() as session:
        # 1. گرفتن اطلاعات ملک جدید
        property_result = await session.execute(
            select(TenantProperty).where(TenantProperty.id == property_id)
        )
        new_property = property_result.scalar_one_or_none()
        
        if not new_property:
            logger.error(f"❌ Property {property_id} not found!")
            stats["errors"].append(f"Property {property_id} not found")
            return stats
        
        logger.info(f"🏠 New property: {new_property.name} ({new_property.price:,} AED, {new_property.property_type})")
        
        # 2. گرفتن tenant برای property_presenter
        tenant_result = await session.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        
        if not tenant:
            logger.error(f"❌ Tenant {tenant_id} not found!")
            stats["errors"].append(f"Tenant {tenant_id} not found")
            return stats
        
        # 3. پیدا کردن لیدهای کولیفای شده که با این ملک match میکنن
        # فیلتر: qualified/hot leads که preferences ذخیره شده دارن
        matching_leads_query = select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.status == LeadStatus.QUALIFIED,
            Lead.budget_min.isnot(None),  # حتماً بودجه ذخیره شده باشه
            Lead.budget_max.isnot(None)
        )
        
        # فیلتر بودجه: lead.budget_min <= property.price <= lead.budget_max * 1.1 (10% flexibility)
        matching_leads_query = matching_leads_query.where(
            Lead.budget_min <= new_property.price,
            Lead.budget_max * 1.1 >= new_property.price  # 10% tolerance
        )
        
        # فیلتر نوع ملک (اگر ذخیره شده باشه)
        if new_property.property_type:
            matching_leads_query = matching_leads_query.where(
                (Lead.property_type == new_property.property_type) |
                (Lead.property_type.is_(None))  # OR no preference saved
            )
        
        # فیلتر تعداد اتاق (اگر ذخیره شده باشه)
        if new_property.bedrooms:
            matching_leads_query = matching_leads_query.where(
                (Lead.bedrooms_min.is_(None)) |  # No bedroom preference
                (Lead.bedrooms_min <= new_property.bedrooms)
            ).where(
                (Lead.bedrooms_max.is_(None)) |  # No bedroom max
                (Lead.bedrooms_max >= new_property.bedrooms)
            )
        
        # اجرای query
        result = await session.execute(matching_leads_query)
        matching_leads = result.scalars().all()
        
        logger.info(f"🎯 Found {len(matching_leads)} matching qualified leads")
        
        # 4. برای هر lead، ملک رو با urgency بفرست
        for lead in matching_leads:
            try:
                # چک کن که اخیراً به این lead ملک نفرستادیم (anti-spam)
                if lead.last_interaction:
                    time_since_last = datetime.utcnow() - lead.last_interaction
                    if time_since_last < timedelta(hours=2):
                        logger.info(f"⏭️ Skipping lead {lead.id} - contacted within 2 hours")
                        stats["leads_skipped"] += 1
                        continue
                
                # تبدیل property به dict format
                property_data = {
                    "id": new_property.id,
                    "name": new_property.name,
                    "price": new_property.price,
                    "location": new_property.location,
                    "bedrooms": new_property.bedrooms,
                    "bathrooms": new_property.bathrooms,
                    "area_sqft": new_property.area_sqft,
                    "property_type": new_property.property_type.value if new_property.property_type else "Apartment",
                    "image_urls": new_property.image_urls or [],
                    "brochure_pdf": new_property.brochure_pdf,
                    "primary_image": new_property.primary_image,
                    "features": new_property.features or [],
                    "description": new_property.full_description or new_property.description,
                    "expected_roi": new_property.expected_roi or 8.5,
                    "rental_yield": new_property.rental_yield or 7.0,
                    "golden_visa_eligible": new_property.golden_visa_eligible,
                    "is_featured": new_property.is_featured,
                    "is_urgent": new_property.is_urgent
                }
                
                # تولید پیام urgency
                lang = lead.language or Language.FA
                urgency_msg = generate_urgency_message(property_data, lang)
                
                # ساخت پیام معرفی
                intro_messages = {
                    Language.FA: f"🔔 **ملک ویژه - مطابق با سلیقه شما!**\n\n{urgency_msg}\n\n",
                    Language.EN: f"🔔 **Exclusive Property - Matches Your Preferences!**\n\n{urgency_msg}\n\n",
                    Language.AR: f"🔔 **عقار حصري - يطابق تفضيلاتك!**\n\n{urgency_msg}\n\n",
                    Language.RU: f"🔔 **Эксклюзивный объект - соответствует вашим предпочтениям!**\n\n{urgency_msg}\n\n"
                }
                
                intro_msg = intro_messages.get(lang, intro_messages[Language.EN])
                
                # ارسال ملک با ROI PDF از طریق property_presenter
                if bot_interface:
                    platform = "telegram" if hasattr(bot_interface, 'application') else "whatsapp"
                    
                    # ارسال پیام معرفی اول
                    if platform == "telegram" and lead.telegram_chat_id:
                        await bot_interface.application.bot.send_message(
                            chat_id=lead.telegram_chat_id,
                            text=intro_msg,
                            parse_mode="Markdown"
                        )
                    elif platform == "whatsapp" and lead.whatsapp_phone:
                        await bot_interface.send_message(lead.whatsapp_phone, intro_msg)
                    
                    # ارسال property با presenter حرفه‌ای
                    await send_property_with_roi(
                        bot_interface=bot_interface,
                        lead=lead,
                        tenant=tenant,
                        property_data=property_data,
                        platform=platform,
                        index=1  # First property in follow-up
                    )
                    
                    logger.info(f"✅ Notified lead {lead.id} ({lead.name}) about new property {new_property.id}")
                    stats["leads_notified"] += 1
                    
                    # آپدیت last_interaction
                    lead.last_interaction = datetime.utcnow()
                    await session.commit()
                else:
                    logger.warning(f"⚠️ No bot_interface provided - skipping lead {lead.id}")
                    stats["leads_skipped"] += 1
                
            except Exception as e:
                logger.error(f"❌ Error notifying lead {lead.id}: {e}")
                stats["errors"].append(f"Lead {lead.id}: {str(e)}")
                stats["leads_skipped"] += 1
    
    logger.info(f"📊 Follow-up complete: {stats['leads_notified']} notified, {stats['leads_skipped']} skipped, {len(stats['errors'])} errors")
    return stats


async def get_matching_leads_count(tenant_id: int, property_id: int) -> int:
    """
    تعداد لیدهایی که با این ملک match میکنن رو برمیگردونه (بدون ارسال پیام).
    مفید برای preview قبل از آپلود.
    
    Returns:
        تعداد لیدهای matching
    """
    async with async_session() as session:
        property_result = await session.execute(
            select(TenantProperty).where(TenantProperty.id == property_id)
        )
        new_property = property_result.scalar_one_or_none()
        
        if not new_property:
            return 0
        
        matching_leads_query = select(Lead).where(
            Lead.tenant_id == tenant_id,
            Lead.status == LeadStatus.QUALIFIED,
            Lead.budget_min.isnot(None),
            Lead.budget_max.isnot(None),
            Lead.budget_min <= new_property.price,
            Lead.budget_max * 1.1 >= new_property.price
        )
        
        if new_property.property_type:
            matching_leads_query = matching_leads_query.where(
                (Lead.property_type == new_property.property_type) |
                (Lead.property_type.is_(None))
            )
        
        result = await session.execute(matching_leads_query)
        matching_leads = result.scalars().all()
        
        return len(matching_leads)
